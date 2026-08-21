# browser demo so people can get roasted without installing slack.
# same brain as the bot (roaster.py), just a different face.

import os
import threading
import time

from flask import Flask, jsonify, request

import md
import roaster

app = Flask(__name__)

# naive per-ip limit. good enough for a free-tier demo, not a bank.
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
    # render sits behind a proxy, so trust its forwarded header first
    ip = request.headers.get("X-Forwarded-For", request.remote_addr).split(",")[0].strip()
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
<title>roasty bot 🔥</title>
<style>
  :root { --bg:#0b0e13; --panel:#11151c; --line:#26303d;
          --blue:#6cb2ff; --blue-hi:#8ec4ff; --ink:#dfe7ef; --dim:#8a97a5; }
  * { box-sizing:border-box; }
  body { background:var(--bg); color:var(--ink); font-family:ui-monospace,monospace;
         max-width:600px; margin:10vh auto; padding:0 20px; line-height:1.55; }
  h1 { color:var(--blue); font-size:1.9rem; margin-bottom:0; letter-spacing:.5px; }
  p.sub { color:var(--dim); margin-top:.4rem; }
  input { width:100%; padding:12px; margin:6px 0 10px; background:var(--panel);
          color:var(--ink); border:1px solid var(--line); border-radius:0; }
  input:focus { outline:none; border-color:var(--blue); }
  button { background:var(--blue); color:#0b0e13; border:none; border-radius:0;
           padding:12px 22px; font-weight:bold; cursor:pointer;
           font-family:inherit; font-size:.95rem; }
  button:hover { background:var(--blue-hi); }
  #out { margin-top:24px; min-height:60px; font-size:1.1rem; color:var(--blue-hi); }
  #out b { color:#ffffff; }  #out code { background:var(--panel);
           border:1px solid var(--line); padding:1px 5px; }
  hr { border:none; border-top:1px solid var(--line); margin:28px 0; }
  footer { color:var(--dim); font-size:.85rem; }
</style>
</head>
<body>
  <h1>roasty bot</h1>
  <p class="sub">the slack bot that roasts people. now in browser form.</p>

  <hr>

  <input id="msg" maxlength="280" placeholder="say something to it...">
  <button onclick="burn('chat')">talk trash</button>

  <p class="sub">or drop a name:</p>
  <input id="who" maxlength="80" placeholder="a name...">
  <button onclick="burn('name')">roast this person</button>

  <div id="out"></div>

  <footer>free tier ai, be patient. 5 burns per minute per person.</footer>

<script>
async function burn(mode) {
  const input = document.getElementById(mode === "name" ? "who" : "msg");
  const out = document.getElementById("out");
  const text = input.value.trim();
  if (!text) { out.textContent = "you have to actually type something."; return; }
  out.textContent = "cooking...";
  try {
    const r = await fetch("/api/roast", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({mode, text})
    });
    const data = await r.json();
    if (data.roast) { out.innerHTML = "🔥 " + data.roast; }
    else { out.textContent = data.error || "the stove broke. try again."; }
  } catch (e) {
    out.textContent = "the stove broke. try again.";
  }
}
</script>
</body>
</html>"""


# the slack side rides along inside this same process. has to live at
# module level — render runs `gunicorn web:app`, which only imports us,
# and an __main__ guard would never fire there.
if (
    os.environ.get("RUN_SLACK_BOT") == "1"
    and os.environ.get("SLACK_BOT_TOKEN")
    and os.environ.get("SLACK_APP_TOKEN")
):
    def run_slack():
        # imports live in here on purpose: bot.py builds its App (and
        # calls auth.test) at import time, so a bad token must only
        # kill this thread, never the whole web service
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
    # render injects PORT, locally we default to 5000
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
