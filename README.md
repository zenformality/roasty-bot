# roasty

a slack bot that roasts people. slash commands, @mentions, dms, plus a small web demo.

it also shows up on its own: when you add it to a channel it says hi (and picks someone), and every ~90 minutes it wanders into one of its channels with an unsolicited roast. set `AMBIENT_MINUTES=0` in `.env` if your workspace can't handle that.

## using it

five slash commands: `/roasty-roast @user`, `/roasty-selfroast`, `/roasty-chat <message>`, `/roasty-ping`, `/roasty-help`.

you can also @mention it anywhere, or dm it whatever you want. dms need no command at all. channels only get responses when it's actually addressed, because bots that reply to everything get exiled from servers fast.

## setup

1. slack app at [api.slack.com/apps](https://api.slack.com/apps), from scratch. enable socket mode, which walks you through making the app-level token (`xapp-`). under oauth & permissions add scopes: `chat:write`, `commands`, `app_mentions:read`, `channels:history`, `channels:read`. install to workspace and grab the bot token (`xoxb-`).
2. under event subscriptions → subscribe to bot events, add `member_joined_channel` and `message.im` (plus `app_mention` via the `app_mentions:read` scope). then create the five slash commands with the exact same names, case-sensitive. slack insists on a request url even though socket mode ignores it entirely, put whatever.
3. free gemini key from [aistudio.google.com/apikey](https://aistudio.google.com/apikey). optional second opinion from [opencode.ai/auth](https://opencode.ai/auth). either one goes in `.env` (copy `.env.example`). both providers race each request; set `GEMINI_MODEL` or `OPENCODE_MODEL` to pin a specific model instead of the built-in chains.

then:

```shell
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python bot.py
```

test somewhere disposable first. not #general. please.

## web demo

same roast engine, browser face:

```shell
python web.py   # -> http://localhost:5000
```

rate limited per ip, since an open roast endpoint on free ai keys gets abused fast.

## render

one free web service can run both the demo and the bot. socket mode doesn't need an open port, just process time, so `web.py` starts the slack connection in a background thread next to flask when `RUN_SLACK_BOT=1`. that's what `render.yaml` sets up: new + → blueprint → this repo, paste keys when asked.

free tier sleeps after ~15 idle minutes which kills the slack socket too, so something has to poke the url forever. cron-job.org hitting your demo url every 5 minutes works well. `.github/workflows/keep-alive.yml` is a backup but github delays scheduled actions by 20-55+ minutes, way past render's nap window, so don't count on it alone. needs `DEMO_URL` in repo secrets.

## hack club nest (no sleeping)

if you're in the Hack Club slack, [nest.hackclub.com](https://nest.hackclub.com) gives you a free always-on VM. no 15-minute naps, no keep-alive hacks. ask @nest in slack to get one if you don't have an account.

```shell
ssh you@nest.hackclub.com
git clone <this repo> ~/roasty-bot
cd ~/roasty-bot
python3 -m venv venv
venv/bin/pip install -r requirements.txt
cp .env.example .env && nano .env
```

the bot runs as a systemd user service, unit file is `nest/roasty.service` here. it runs both the demo and the slack side, same trick as on render:

```shell
cp nest/roasty.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now roasty
journalctl --user -u roasty -f
```

for the web demo at `https://<your-username>.hackclub.app`, put this in `~/Caddyfile`:

```
<your-username>.hackclub.app {
    reverse_proxy localhost:8080
}
```

caddy picks up the change itself; if your subdomain stays stubborn the [nest guides](https://guides.hackclub.app) cover it. updating later: `git pull && systemctl --user restart roasty`.

## problems

token swapped? happens constantly, been there. `xoxb-` goes to `SLACK_BOT_TOKEN`, `xapp-` to `SLACK_APP_TOKEN`. terminal logs will tell you which one is wrong.

getting canned roasts means both providers failed; the logs name the exact model and why. 503s are free-tier popularity and clear up on their own, the bot retries meanwhile.

command not found means the name in the slack dashboard doesn't match the code character for character.
