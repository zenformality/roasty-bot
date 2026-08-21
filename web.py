# browser demo so people can get roasted without installing slack.
# same brain as the bot (roaster.py), just a different face.

import os
import time

from flask import Flask, jsonify, request

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
        return jsonify(roast=roaster.generate_roast(text))
    return jsonify(roast=roaster.chat_roast(text))


PAGE = """<!doctype html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>roasty bot 🔥</title>
<style>
  body { background:#0e0e10; color:#f2f2f2; font-family:ui-monospace,monospace;
         max-width:620px; margin:8vh auto; padding:0 20px; }
  h1 { font-size:2rem; margin-bottom:0; }
  p.sub { color:#999; margin-top:.4rem; }
  .box { width:100%; box-sizing:border-box; padding:12px; margin:6px 0;
         background:#1a1a1d; color:#eee; border:1px solid #333; border-radius:8px; }
  button { background:#ff5722; color:#fff; border:none; padding:10px 18px;
           border-radius:8px; cursor:pointer; font-weight:bold; }
  button:hover { background:#ff7043; }
  #out { margin-top:22px; min-height:60px; font-size:1.15rem; line-height:1.5;
         color:#ffb74d; white-space:pre-wrap; }
  footer { margin-top:40px; color:#666; font-size:.85rem; }
</style>
</head>
<body>
  <h1>roasty bot 🔥</h1>
  <p class="sub">the slack bot that roasts people. now in browser form.</p>

  <input id="msg" class="box" maxlength="280" placeholder="say something to it...">
  <button onclick="burn('chat')">talk trash</button>

  <p class="sub">or drop a name and let it rip:</p>
  <input id="who" class="box" maxlength="80" placeholder="a name...">
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
    out.textContent = data.roast ? "🔥 " + data.roast : data.error;
  } catch (e) {
    out.textContent = "the stove broke. try again.";
  }
}
</script>
</body>
</html>"""


if __name__ == "__main__":
    # render injects PORT, locally we default to 5000
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
