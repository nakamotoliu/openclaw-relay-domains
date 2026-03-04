# OpenClaw Browser Relay Domains Skill

Single shared version (no separate local/public scripts).

## What it does
- Adds domain to `src/manifest.json` as `https://*.domain/*`
- Adds domain to `AUTO_ATTACH_DOMAINS` in `src/background.js`
- Opens `chrome://extensions/` so user can click Reload

## Command

```bash
python3 ~/clawd/skills/openclaw-browser-relay-domains/scripts/add_domain.py "example.com"
```

## Local variables (safe pattern)
1. Copy `config.example.json` to `config.local.json`
2. Put machine-specific values in `config.local.json` (repo path, browser app, token env var)
3. `config.local.json` is ignored by git (`.gitignore`) and must NOT be uploaded to GitHub

## Optional flags
- `--repo <path>`: override relay repo path
- `--open-extensions`: force open `chrome://extensions/`
- `--open-token-tab`: open token helper tab from env var
- `--browser-app "Google Chrome"`: specify browser app name on macOS

## Version bump rule (mandatory)
If relay extension source files are changed (`projects/openclaw-browser-relay-rewrite/src/*`), bump `manifest.json` version every time before asking user to Reload.

## Usage rule
When asked to add relay auto-attach domain, use this script only.
