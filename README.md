# RoastyBot 🔥

a slack bot that roasts people. you tag, it burns.

gemini free tier does the thinking, opencode zen covers when google is having a day, and if both are down there's a stash of pre-written insults so the bot is never speechless.

## Commands

| Command | What it does |
| --- | --- |
| `/roasty-ping` | Health check |
| `/roasty-roast @user` | Roasts whoever got tagged |
| `/roasty-selfroast` | Roasts the person who typed it |
| `/roasty-chat <message>` | Free chat in roast mode |
| `/roasty-help` | Lists all commands |

You can also just `@RoastyBot` mention it anywhere and it will fire back.

## Files

- `bot.py` — main Slack bot: slash commands + mention listener (Socket Mode)
- `roaster.py` — Gemini roast engine (`generate_roast`, `chat_roast`, `selfroast`)
- `responses.py` — canned fallback roasts, help text, ping template

## Setup

### 1. Create the Slack app

1. Go to <https://api.slack.com/apps> → **Create New App → From scratch**, pick your workspace.
2. **Socket Mode** → toggle on.
3. **Basic Information** → App-Level Tokens → generate a token with the `connections:write` scope (starts with `xapp-`). This is your `SLACK_APP_TOKEN`.
4. **OAuth & Permissions** → Bot Token Scopes → add:
   - `chat:write`
   - `commands`
   - `app_mentions:read`
   - `channels:history`
5. **Install App** → Install to Workspace → copy the Bot User OAuth Token (starts with `xoxb-`). This is your `SLACK_BOT_TOKEN`.
6. **Slash Commands** → create each command from the table above. Prefix matters — keep the exact names (`/roasty-ping`, etc.).

> Tip: don't use generic names like `/ping` in big workspaces — they collide with other bots.

### 2. Get a Gemini API key

Grab a free key at <https://aistudio.google.com/apikey> — no billing required.

The bot tries these free-tier models in order and uses the first that works:

1. `gemini-3.7-flash`
2. `gemini-3.5-flash-lite`
3. `gemini-2.5-flash-lite`

To pin a specific one, set `GEMINI_MODEL=<model-id>` in `.env`.

**Optional extra fallback:** get a free OpenCode Zen key at <https://opencode.ai/auth> (no credit card) and set `OPENCODE_API_KEY` in `.env`. When every Gemini model is busy or failing, the bot tries OpenCode Zen before serving canned roasts. Zen itself is a chain — `deepseek-v4-flash-free` → `laguna-s-2.1-free` → `big-pickle` — since individual free models go up and down often. Setting `OPENCODE_MODEL=<id>` overrides the whole Zen chain with one model (`curl https://opencode.ai/zen/v1/models` to list options).

### 3. Configure & run locally

```shell
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Fill in `.env`:

```plaintext
SLACK_BOT_TOKEN=xoxb-...
SLACK_APP_TOKEN=xapp-...
GEMINI_API_KEY=...
OPENCODE_API_KEY=...
```

Start the bot:

```shell
python bot.py
```

Test it in a spam/test channel — not in busy shared channels.

## Deploy 24/7 (Hack Club Nest)

```shell
git clone https://github.com/<you>/roasty-bot
cd roasty-bot
python3 -m venv venv
venv/bin/pip install -r requirements.txt
nano .env   # paste your tokens again
```

Create `/etc/systemd/system/roastybot.service`:

```ini
[Unit]
Description=RoastyBot
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
Restart=always
RestartSec=5
WorkingDirectory=/root/roasty-bot
ExecStart=/root/roasty-bot/venv/bin/python bot.py

[Install]
WantedBy=multi-user.target
```

Then:

```shell
systemctl daemon-reload
systemctl enable --now roastybot.service
journalctl -u roastybot.service -f
```

## Troubleshooting

- **Nothing happens on a command** — check the terminal logs; verify `xoxb-` is in `SLACK_BOT_TOKEN` and `xapp-` is in `SLACK_APP_TOKEN`.
- **Slash command unknown** — the name in the Slack dashboard must match the code exactly (case-sensitive).
- **Canned roasts instead of AI roasts** — Gemini failed or `GEMINI_API_KEY` is missing; check logs for warnings.
- **`503 UNAVAILABLE / high demand`** — Google's free tier is overloaded. The bot auto-retries each model once, then moves to the next model, and finally serves a canned roast. Usually temporary.
