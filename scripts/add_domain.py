#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import platform
import re
import subprocess
from pathlib import Path
from urllib.parse import quote


def normalize_domain(raw: str) -> str:
    d = raw.strip().lower()
    d = re.sub(r"^https?://", "", d)
    d = d.split("/")[0]
    if d.startswith("*."):
        d = d[2:]
    return d


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_json(path: Path, data: dict):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def detect_repo(cli_repo: str | None, cfg: dict) -> Path:
    if cli_repo:
        return Path(cli_repo).expanduser().resolve()

    cfg_repo = str(cfg.get("relayRepo", "")).strip()
    if cfg_repo:
        return Path(cfg_repo).expanduser().resolve()

    env_repo = os.environ.get("RELAY_REPO", "").strip()
    if env_repo:
        return Path(env_repo).expanduser().resolve()

    cwd = Path.cwd()
    if (cwd / "src" / "manifest.json").exists() and (cwd / "src" / "background.js").exists():
        return cwd

    raise SystemExit("❌ Cannot detect relay repo. Use --repo or set relayRepo in config.local.json")


def update_manifest(manifest_path: Path, domain: str) -> str:
    manifest = load_json(manifest_path)
    host_permissions = manifest.setdefault("host_permissions", [])
    pattern = f"https://*.{domain}/*"

    if pattern in host_permissions:
        return f"⚡ {pattern} already in manifest.json"

    host_permissions.append(pattern)
    save_json(manifest_path, manifest)
    return f"✅ Added {pattern} to manifest.json"


def update_background(background_path: Path, domain: str) -> str:
    content = background_path.read_text(encoding="utf-8")
    pattern = r"const AUTO_ATTACH_DOMAINS = \[([^\]]*)\]"
    m = re.search(pattern, content)
    if not m:
        return "❌ Could not find AUTO_ATTACH_DOMAINS in background.js"

    domains = [x.strip().strip("'\"") for x in m.group(1).split(",") if x.strip()]
    if domain in domains:
        return f"⚡ {domain} already in background.js AUTO_ATTACH_DOMAINS"

    domains.append(domain)
    replacement = f"const AUTO_ATTACH_DOMAINS = [{', '.join([repr(d) for d in domains])}]"
    content = re.sub(pattern, replacement, content)
    background_path.write_text(content, encoding="utf-8")
    return f"✅ Added {domain} to AUTO_ATTACH_DOMAINS in background.js"


def open_url(url: str, browser_app: str | None):
    system = platform.system().lower()
    try:
        if system == "darwin":
            if browser_app:
                subprocess.run(["open", "-a", browser_app, url], check=False)
            else:
                subprocess.run(["open", url], check=False)
        elif system == "windows":
            os.startfile(url)  # type: ignore[attr-defined]
        else:
            subprocess.run(["xdg-open", url], check=False)
    except Exception:
        pass


def main():
    skill_dir = Path(__file__).resolve().parents[1]
    default_config = skill_dir / "config.local.json"

    parser = argparse.ArgumentParser(description="Add auto-attach domain for OpenClaw Browser Relay")
    parser.add_argument("domain", help="Domain like youtube.com")
    parser.add_argument("--repo", help="Relay repo path")
    parser.add_argument("--config", default=str(default_config), help="Local config path")
    parser.add_argument("--open-extensions", action="store_true", help="Open chrome://extensions/")
    parser.add_argument("--open-token-tab", action="store_true", help="Open token helper tab")
    parser.add_argument("--browser-app", help="Browser app name on macOS, e.g. 'Google Chrome'")
    args = parser.parse_args()

    domain = normalize_domain(args.domain)
    if not domain or "." not in domain:
        raise SystemExit(f"❌ Invalid domain: {args.domain}")

    config_path = Path(args.config).expanduser().resolve()
    cfg = load_json(config_path)

    repo = detect_repo(args.repo, cfg)
    manifest_path = repo / "src" / "manifest.json"
    background_path = repo / "src" / "background.js"

    if not manifest_path.exists() or not background_path.exists():
        raise SystemExit("❌ Missing src/manifest.json or src/background.js in relay repo")

    print(update_manifest(manifest_path, domain))
    print(update_background(background_path, domain))

    open_extensions = args.open_extensions or bool(cfg.get("openExtensionsAfterUpdate", True))
    open_token = args.open_token_tab or bool(cfg.get("openTokenHelperTab", False))
    browser_app = args.browser_app or str(cfg.get("browserApp", "Google Chrome"))

    if open_extensions:
        open_url("chrome://extensions/", browser_app)
        print("✅ Opened chrome://extensions (please click Reload)")

    if open_token:
        token_env = str(cfg.get("tokenEnvVar", "OPENCLAW_GATEWAY_TOKEN"))
        token = os.environ.get(token_env, "").strip()
        if token:
            data_url = "data:text/plain," + quote("GATEWAY_TOKEN\n" + token + "\n")
            open_url(data_url, browser_app)
            print(f"✅ Opened token helper tab from ${token_env}")
        else:
            print(f"⚠️ ${token_env} not found; skipped token helper tab")


if __name__ == "__main__":
    main()
