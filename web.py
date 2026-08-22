import os
import threading
import time

from flask import Flask, jsonify, request

import md
import roaster

app = Flask(__name__)

LIMIT = int(os.environ.get("ROASTS_PER_MINUTE", "5"))
MAX_CHARS = 280
_hits = {}


def rate_limited(ip):
    now = time.time()
    recent = [t for t in _hits.get(ip, []) if now - t < 60]
    if len(recent) >= LIMIT:
        _hits[ip] = recent
        return True
    recent.append(now)
    _hits[ip] = recent
    return False


@app.get("/")
def home():
    return PAGE


@app.post("/api/roast")
def roast():
    ip = request.headers.get("X-Forwarded-For", request.remote_addr or "").split(",")[0].strip()
    if rate_limited(ip):
        return jsonify(error="slow down, you'll start a fire. try again in a minute."), 429

    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()[:MAX_CHARS]
    mode = data.get("mode")

    if not text:
        return jsonify(error="give me something to work with"), 400

    if mode == "name":
        return jsonify(roast=md.to_html(roaster.generate_roast(text)))
    return jsonify(roast=md.to_html(roaster.chat_roast(text)))


PAGE = """<!doctype html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>roasty</title>
<style>
body { background:#101214; color:#ccc; font-family:monospace; max-width:560px;
       margin:80px auto; padding:0 16px; line-height:1.5; }
h1 { color:#79b8ff; margin-bottom:4px; }
input { width:100%; box-sizing:border-box; padding:10px; margin:8px 0;
        background:#191c20; border:1px solid #333; color:#ddd; font-family:inherit; }
button { background:#79b8ff; color:#101214; border:none; padding:10px 18px;
         font-family:inherit; font-weight:bold; cursor:pointer; margin-bottom:20px; }
button:hover { background:#a3ccff; }
#out { margin-top:10px; min-height:50px; font-size:17px; color:#a3ccff; }
hr { border:none; border-top:1px solid #333; margin:24px 0; }
footer { color:#777; font-size:13px; margin-top:48px; }
</style>
</head>
<body>
<h1>roasty bot</h1>
<p>the slack bot that roasts people, now yelling at you from a browser.</p>

<hr>

<input id="msg" maxlength="280" placeholder="say something to it..."><br>
<button onclick="burn('chat')">talk trash</button>

<p>or drop a name:</p>
<input id="who" maxlength="80" placeholder="a name..."><br>
<button onclick="burn('name')">roast this person</button>

<div id="out"></div>

<footer>free tier ai, give it a sec. 5 burns/min per person.</footer>

<script>
function burn(mode) {
  var input = document.getElementById(mode == "name" ? "who" : "msg");
  var out = document.getElementById("out");
  if (!input.value.trim()) {
    out.textContent = "type something first.";
    return;
  }
  out.textContent = "cooking...";
  fetch("/api/roast", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({mode: mode, text: input.value})
  })
  .then(r => r.json())
  .then(d => out.innerHTML = d.roast ? "🔥 " + d.roast : (d.error || "hmm that broke"))
  .catch(() => out.textContent = "hmm that broke");
}
</script>
</body>
</html>"""


if (
    os.environ.get("RUN_SLACK_BOT") == "1"
    and os.environ.get("SLACK_BOT_TOKEN")
    and os.environ.get("SLACK_APP_TOKEN")
):
    def run_slack():
        try:
            import bot as slack_side
            from slack_bolt.adapter.socket_mode import SocketModeHandler

            SocketModeHandler(
                slack_side.app, os.environ["SLACK_APP_TOKEN"]
            ).connect()
            print("slack side connected", flush=True)
        except Exception as e:
            print(f"slack side failed to connect: {e}", flush=True)

    threading.Thread(target=run_slack, daemon=True).start()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
