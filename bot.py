import logging
import os
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

MENTION = re.compile(r"<@([UW][A-Z0-9]+)")


def name_of(client, user_id):
    try:
        u = client.users_info(user=user_id)["user"]
        p = u.get("profile", {})
        return p.get("display_name") or p.get("real_name") or u.get("name") or "buddy"
    except Exception:
        return "buddy"


def later(fn):
    threading.Thread(target=fn, daemon=True).start()


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


if __name__ == "__main__":
    print("roasty is up. ctrl+c to end the carnage")
    SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start()
