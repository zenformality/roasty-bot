# roasty bot 🔥

a slack bot that roasts people. you tag, it burns.

gemini's free tier does the thinking, opencode zen covers when google is having a day, and when both are down there's a stash of pre-written insults so it's never speechless.

## what it does

- `/roasty-ping` — health check
- `/roasty-roast @user` — ruin someone's day
- `/roasty-selfroast` — ruin your own day
- `/roasty-chat <message>` — chat mode, but rude
- `/roasty-help` — this menu

you can also just @mention it anywhere. it will find you.

## the files

- `bot.py` — slack plumbing: slash commands + mention listener (socket mode)
- `roaster.py` — the brain. gemini first, opencode zen second, canned insults last
- `responses.py` — backup ammo

## setting it up

### slack part (~5 min)

1. make an app at [api.slack.com/apps](https://api.slack.com/apps) → from scratch → pick your workspace
2. turn on **socket mode** (left sidebar). it walks you through making an app-level token with `connections:write` — that's your `SLACK_APP_TOKEN` (`xapp-...`)
3. **oauth & permissions** → add bot scopes: `chat:write`, `commands`, `app_mentions:read`, `channels:history`
4. install to workspace → copy the bot token (`xoxb-...`) → that's `SLACK_BOT_TOKEN`
5. create the five slash commands with the exact names above. case matters.
   slack demands a request url even though socket mode ignores it — just put anything

tip: don't use generic names like `/ping` in big workspaces. other bots took them years ago and slack will quietly break yours.

### ai keys

grab a free gemini key at [aistudio.google.com/apikey](https://aistudio.google.com/apikey) — no credit card. the bot walks down `gemini-3.7-flash → 3.5-flash-lite → 2.5-flash-lite` and uses whichever one isn't overloaded. set `GEMINI_MODEL` in `.env` to pin a specific one.

optional but nice: free opencode zen key at [opencode.ai/auth](https://opencode.ai/auth) → `OPENCODE_API_KEY` in `.env`. if every gemini model is busy, it tries zen before falling back to canned lines. zen is its own chain (`deepseek-v4-flash-free → laguna-s-2.1-free → big-pickle`) because individual free models go up and down constantly. `curl https://opencode.ai/zen/v1/models` lists what's alive today; set `OPENCODE_MODEL` to pin one.

### running it

```shell
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

copy `.env.example` to `.env` and paste your tokens in:

```plaintext
SLACK_BOT_TOKEN=xoxb-...
SLACK_APP_TOKEN=xapp-...
GEMINI_API_KEY=...
OPENCODE_API_KEY=...   # optional
```

then:

```shell
python bot.py
```

test in #bot-spam or your own channel. not in #general. please.

## try it without slack

same roast engine, browser face:

```shell
python web.py   # -> http://localhost:5000
```

<!-- drop a gif of the bot doing its thing at docs/demo.gif and uncomment:
<img src="docs/demo.gif" alt="roasty in action" width="600">
-->

### putting it on render (free)

push this repo to github, then on [render.com](https://render.com): **new + → blueprint** → pick the repo. it reads `render.yaml` and does the rest. paste `GEMINI_API_KEY` / `OPENCODE_API_KEY` when asked — never commit them.

free tier sleeps after ~15 idle minutes, so the first visitor eats a ~30s cold start. that's the price of $0.

## keeping it alive 24/7 (nest)

clone the repo, recreate `.env` by hand (it's gitignored on purpose), then let systemd babysit it:

```shell
git clone https://github.com/<you>/roasty-bot
cd roasty-bot
python3 -m venv venv
venv/bin/pip install -r requirements.txt
nano .env   # paste your tokens again
```

`/etc/systemd/system/roastybot.service`:

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

```shell
systemctl daemon-reload
systemctl enable --now roastybot.service
journalctl -u roastybot.service -f   # watch it work
```

## when stuff breaks

- **nothing happens on a command** — terminal logs first. then check `xoxb-` went into `SLACK_BOT_TOKEN` and `xapp-` into `SLACK_APP_TOKEN`. they get swapped constantly (been there).
- **slash command unknown** — the name in the slack dashboard has to match the code exactly. case-sensitive.
- **canned roasts instead of ai ones** — gemini failed or the key is missing. the logs say exactly which model died and why.
- **503 / high demand** — free tier being popular again. the bot retries each model once, moves on, worst case serves canned ammo. usually clears up on its own.
