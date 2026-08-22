# roast engine. two providers race in parallel, first useful answer wins,
# and whichever model answered last gets tried first next round so we stop
# paying dead models' rent on every single roast.

import logging
import os
import queue
import threading
import time

import httpx
from google import genai
from google.genai import errors as genai_errors
from google.genai import types

from responses import fallback_chat, fallback_roast, fallback_selfroast

log = logging.getLogger("roasty.ai")

GEMINI_MODELS = (
    "gemini-3.5-flash-lite",    # survived google's culling, fast, big free quota
    "gemini-3.7-flash",         # fancy but flaky from shared ips
)

ZEN_MODELS = (
    "laguna-s-2.1-free",        # reliable-ish
    "deepseek-v4-flash-free",   # user's pick, goes down a lot
    "big-pickle",               # popular, rate limited sometimes
)

# the voice: merciless, but never actually harmful.
# the limits section is non-negotiable unless you enjoy getting reported
# to workspace admins.
SYSTEM_PROMPT = (
    "You are RoastyBot, a merciless insult comic haunting a Slack workspace. "
    "Mercy is not in your vocabulary. You leave people speechless.\n"
    "Style:\n"
    "- Go for the jugular. One brutal line beats a paragraph. Two sentences max.\n"
    "- Aim at egos, habits, coding skills, life choices, taste, effort, general vibes.\n"
    "- Weapons: fake compliments, absurd comparisons, devastating specificity, "
    "disappointed-parent energy, cold professional contempt.\n"
    "- Roast-comic rules: personal, confident, relentless. The crueler AND funnier, "
    "the better. Punch UP at their ego, never down.\n"
    "- Never apologize, never soften, no disclaimers, no comfort emojis.\n"
    "Hard limits (never break these):\n"
    "- No slurs, racism, sexism, homophobia, transphobia, religion attacks.\n"
    "- Nothing sexual. Nothing about weight, disabilities or mental health.\n"
    "- No real threats or harassment. You're a comedian, not a menace."
)

TRANSIENT = {429, 500, 502, 503}
ATTEMPTS = 2          # tries per model before moving on
RETRY_WAIT = 0.8      # seconds between retries
ZEN_TIMEOUT = 10
ASK_DEADLINE = 12     # whole race gets this long, then canned lines take over

_gemini_start_at = 0  # index of the model that answered last time
_zen_start_at = 0
_http = None          # shared client, keeps tls connections warm

_client = None
_gemini_dead = False


def http():
    global _http
    if _http is None:
        _http = httpx.Client(timeout=ZEN_TIMEOUT)
    return _http


def gemini_models():
    override = os.environ.get("GEMINI_MODEL")
    return (override,) if override else GEMINI_MODELS


def zen_models():
    override = os.environ.get("OPENCODE_MODEL")
    return (override,) if override else ZEN_MODELS


def get_client():
    global _client, _gemini_dead
    if _client:
        return _client
    if _gemini_dead:
        return None
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        log.warning("no GEMINI_API_KEY, living on canned roasts")
        _gemini_dead = True
        return None
    try:
        _client = genai.Client(api_key=key)
    except Exception as e:
        log.error("gemini init failed (%s), skipping it from now on", e)
        _gemini_dead = True
    return _client


def ask(prompt):
    # both providers fire at the same time; first useful text wins.
    # losers just finish in their corner, nobody waits for them.
    answers = queue.Queue()

    def run(provider):
        try:
            text = provider(prompt)
        except Exception as e:
            log.warning("provider blew up: %s", e)
            return
        if text:
            answers.put(text)

    threading.Thread(target=run, args=(ask_gemini,), daemon=True).start()
    threading.Thread(target=run, args=(ask_zen,), daemon=True).start()

    deadline = time.time() + ASK_DEADLINE
    while True:
        left = deadline - time.time()
        if left <= 0:
            log.warning("both providers took too long, serving canned")
            return None
        try:
            return answers.get(timeout=left)
        except queue.Empty:
            return None


def ask_gemini(prompt):
    global _gemini_start_at
    client = get_client()
    if client is None:
        return None
    models = gemini_models()
    # start from whoever won last round instead of always paying
    # the first model's failure toll again
    for off in range(len(models)):
        i = (_gemini_start_at + off) % len(models)
        text = try_gemini_model(client, models[i], prompt)
        if text:
            _gemini_start_at = i
            return text
    log.warning("every gemini model failed")
    return None


def try_gemini_model(client, model, prompt):
    for attempt in range(1, ATTEMPTS + 1):
        try:
            out = client.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    temperature=1.3,
                    max_output_tokens=160,  # two sentences, not an essay
                ),
            )
            text = (out.text or "").strip()
            if not text:
                log.warning("gemini %s said nothing useful", model)
                return None
            return text
        except genai_errors.APIError as e:
            if e.code not in TRANSIENT:
                # bad key / bad request -> retrying won't help
                log.warning("gemini %s dead (%s), next model", model, e.code)
                return None
            if attempt < ATTEMPTS:
                log.info("gemini %s busy (%s), retry in %.1fs", model, e.code, RETRY_WAIT)
                time.sleep(RETRY_WAIT)
            else:
                log.warning("gemini %s still busy after %d tries", model, ATTEMPTS)
                return None
        except Exception as e:
            if attempt < ATTEMPTS:
                time.sleep(RETRY_WAIT)
            else:
                log.warning("gemini %s gave up: %s", model, e)
                return None


def ask_zen(prompt):
    global _zen_start_at
    key = os.environ.get("OPENCODE_API_KEY")
    if not key:
        return None
    url = os.environ.get("OPENCODE_BASE_URL", "https://opencode.ai/zen/v1").rstrip("/")
    headers = {"Authorization": f"Bearer {key}"}
    models = zen_models()
    for off in range(len(models)):
        i = (_zen_start_at + off) % len(models)
        text = try_zen_model(url + "/chat/completions", headers, models[i], prompt)
        if text:
            _zen_start_at = i
            return text
    log.warning("every zen model failed")
    return None


def try_zen_model(url, headers, model, prompt):
    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "temperature": 1.3,
        "max_tokens": 200,
    }
    for attempt in range(1, ATTEMPTS + 1):
        try:
            r = http().post(url, json=body, headers=headers)
            if r.status_code == 200:
                try:
                    text = (r.json()["choices"][0]["message"]["content"] or "").strip()
                except (ValueError, KeyError, IndexError):
                    log.warning("zen %s sent weird json", model)
                    return None
                if not text:
                    log.warning("zen %s returned empty text", model)
                    return None
                return text
            if r.status_code in TRANSIENT and attempt < ATTEMPTS:
                log.info("zen %s busy (%s), retry in %.1fs", model, r.status_code, RETRY_WAIT)
                time.sleep(RETRY_WAIT)
                continue
            log.warning("zen %s failed (%s), next model", model, r.status_code)
            return None
        except httpx.HTTPError as e:
            if attempt < ATTEMPTS:
                time.sleep(RETRY_WAIT)
            else:
                log.warning("zen %s network fail: %s", model, e)
                return None


# ---- the three public moves ----

def generate_roast(name):
    return ask(
        f'Roast a Slack user named "{name}". One line. Make it hurt, in the funny way.'
    ) or fallback_roast(name)


def chat_roast(message):
    return ask(
        f'A Slack user says: "{message}". Stay in character as RoastyBot: respond '
        "with witty contempt — mock the message, the delivery, the audacity. If they "
        "asked a question, answer it rudely. Two sentences tops."
    ) or fallback_chat()


def selfroast(username):
    return ask(
        f'"{username}" asked their own bot to roast them. They volunteered for this. '
        "Oblige. Go hard, stay funny."
    ) or fallback_selfroast(username)
