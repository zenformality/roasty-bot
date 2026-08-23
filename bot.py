import logging
import os
import random
import re
import threading
import time

from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

import md
import roaster
from responses import HELP_TEXT, PING_TEXT

load_dotenv()
log = logging.getLogger("roasty")

app = App(token=os.environ["SLACK_BOT_TOKEN"])
BOT_ID = app.client.auth_test()["user_id"]

MENTION = re.compile(r"<@([UW][A-Z0-9]+)")
AMBIENT_MINUTES = float(os.environ.get("AMBIENT_MINUTES", "90"))


def name_of(client, user_id):
    try:
        u = client.users_info(user=user_id)["user"]
        p = u.get("profile", {})
        return p.get("display_name") or p.get("real_name") or u.get("name") or "buddy"
    except Exception:
        return "buddy"


def later(fn):
    threading.Thread(target=fn, daemon=True).start()


def humans_in(client, channel):
    try:
        ids = [u for u in client.conversations_members(channel=channel, limit=200)["members"] if u != BOT_ID]
        if ids:
            return ids
    except Exception:
        pass
    try:
        hist = client.conversations_history(channel=channel, limit=100)["messages"]
        return list({m["user"] for m in hist if m.get("user") and m.get("user") != BOT_ID})
    except Exception:
        return []


@app.command("/roasty-ping")
def ping(ack, respond):
    start = time.perf_counter()
    ack()
    ms = int((time.perf_counter() - start) * 1000)
    respond(response_type="in_channel", text=PING_TEXT.format(latency=ms))


@app.command("/roasty-roast")
def roast(ack, respond, command, client):
    ack()
    hit = MENTION.search(command.get("text", ""))
    if not hit:
        respond(response_type="in_channel", text="tag your victim first → `/roasty-roast @someone`")
        return
    victim = name_of(client, hit.group(1))

    def burn():
        try:
            respond(response_type="in_channel", text=f"hey {victim}! {md.to_slack(roaster.generate_roast(victim))}")
        except Exception as e:
            log.error("roast blew up: %s", e)
            respond(response_type="in_channel", text=f"hey {victim}! you broke the bot. impressive.")

    later(burn)


@app.command("/roasty-selfroast")
def selfroast(ack, respond, command, client):
    ack()
    who = name_of(client, command["user_id"])

    def burn():
        try:
            respond(response_type="in_channel", text=md.to_slack(roaster.selfroast(who)))
        except Exception as e:
            log.error("selfroast blew up: %s", e)
            respond(response_type="in_channel", text="the roast engine died mid-sentence. even that is your fault.")

    later(burn)


@app.command("/roasty-chat")
def chat(ack, respond, command):
    ack()
    msg = command.get("text", "").strip()
    if not msg:
        respond(response_type="in_channel", text="say something first → `/roasty-chat hello`")
        return

    def burn():
        try:
            respond(response_type="in_channel", text=md.to_slack(roaster.chat_roast(msg)))
        except Exception as e:
            log.error("chat blew up: %s", e)
            respond(response_type="in_channel", text="my comeback was so good it crashed me. you're welcome.")

    later(burn)


@app.command("/roasty-help")
def help_menu(ack, respond):
    ack()
    respond(response_type="in_channel", text=HELP_TEXT)


@app.event("app_mention")
def mentioned(event, say, client):
    text = MENTION.sub("", event.get("text", "")).strip()

    def burn():
        try:
            if text:
                say(text=md.to_slack(roaster.chat_roast(text)))
            else:
                say(text=md.to_slack(roaster.generate_roast(name_of(client, event.get("user", "")))))
        except Exception as e:
            log.error("mention blew up: %s", e)
            say(text="i had something devastating ready. the internet ate it.")

    later(burn)


@app.event("message")
def dmed(event, say):
    if event.get("channel_type") != "im":
        return
    if event.get("bot_id") or event.get("subtype") or not (event.get("text") or "").strip():
        return

    def burn():
        try:
            say(text=md.to_slack(roaster.chat_roast(event["text"].strip())))
        except Exception as e:
            log.error("dm blew up: %s", e)
            say(text="my comeback was so good it crashed me. you're welcome.")

    later(burn)


@app.event("member_joined_channel")
def joined(event, say, client):
    if event.get("user") != BOT_ID:
        return

    def burn():
        try:
            uid = event.get("inviter")
            if not uid or uid == BOT_ID:
                pool = humans_in(client, event["channel"])
                uid = random.choice(pool) if pool else None
            if uid:
                name = name_of(client, uid)
                say(text=f"well well well. thanks for letting me in, {name}. {md.to_slack(roaster.generate_roast(name))}")
            else:
                say(text="hi. i'm roasty. i live here now.")
        except Exception as e:
            log.error("join blew up: %s", e)

    later(burn)


def ambient():
    while True:
        time.sleep(AMBIENT_MINUTES * 60 * random.uniform(0.75, 1.25))
        try:
            chans = [
                c["id"]
                for c in app.client.conversations_list(
                    types="public_channel", exclude_archived=True, limit=200
                )["channels"]
                if c.get("is_member")
            ]
            random.shuffle(chans)
            for ch in chans[:4]:
                pool = humans_in(app.client, ch)
                if not pool:
                    continue
                name = name_of(app.client, random.choice(pool))
                app.client.chat_postMessage(
                    channel=ch,
                    text=f"nobody asked but {name}: {md.to_slack(roaster.generate_roast(name))}",
                )
                break
        except Exception as e:
            log.error("ambient blew up: %s", e)


if AMBIENT_MINUTES > 0:
    threading.Thread(target=ambient, daemon=True).start()


if __name__ == "__main__":
    print("roasty is up. ctrl+c to end the carnage")
    SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start()
