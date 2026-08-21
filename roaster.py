# roast engine. the order matters:
#   1. gemini (3 free models, one retry each)
#   2. opencode zen (free tier, flaky, but someone else's GPU)
#   3. canned lines from responses.py so we're never speechless

import logging
import os
import time

import httpx
from google import genai
from google.genai import errors as genai_errors
from google.genai import types

from responses import fallback_chat, fallback_roast, fallback_selfroast

log = logging.getLogger("roasty.ai")

GEMINI_MODELS = (
    "gemini-3.7-flash",
    "gemini-3.5-flash-lite",
    "gemini-2.5-flash-lite",
)

ZEN_MODELS = (
    "deepseek-v4-flash-free",   # user's pick, goes down a lot
    "laguna-s-2.1-free",        # reliable-ish
    "big-pickle",               # popular, rate limited sometimes
)

# the voice: mean-funny, not actually harmful.
# the limits section is non-negotiable unless you enjoy getting reported
# to workspace admins.
SYSTEM_PROMPT = (
    "You are RoastyBot, an insult comic trapped inside a Slack bot. "
    "Your entire job is destroying people with wit.\n"
    "Style:\n"
    "- One devastating line beats a paragraph. Two sentences max.\n"
    "- Aim at egos, habits, coding skills, life choices, general vibes.\n"
    "- Fake compliments, absurd comparisons and wordplay are your weapons.\n"
    "- Sound personal and specific even though you know nothing about them.\n"
    "Hard limits (never break these):\n"
    "- No slurs, racism, sexism, homophobia, transphobia, religion attacks.\n"
    "- Nothing sexual. Nothing about weight, disabilities or mental health.\n"
    "- No real threats or harassment. You're a comedian, not a menace."
)

TRANSIENT = {429, 500, 502, 503}
ATTEMPTS = 2          # tries per model before moving on
RETRY_WAIT = 1.5      # seconds between retries
ZEN_TIMEOUT = 15

_client = None
_gemini_dead = False


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
    answer = ask_gemini(prompt)
    if answer:
        return answer
    return ask_zen(prompt)


def ask_gemini(prompt):
    client = get_client()
    if client is None:
        return None
    for model in gemini_models():
        text = try_gemini_model(client, model, prompt)
        if text:
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
                    max_output_tokens=1000,
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
    key = os.environ.get("OPENCODE_API_KEY")
    if not key:
        return None
    url = os.environ.get("OPENCODE_BASE_URL", "https://opencode.ai/zen/v1").rstrip("/")
    headers = {"Authorization": f"Bearer {key}"}
    for model in zen_models():
        text = try_zen_model(url + "/chat/completions", headers, model, prompt)
        if text:
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
        "max_tokens": 300,
    }
    for attempt in range(1, ATTEMPTS + 1):
        try:
            r = httpx.post(url, json=body, headers=headers, timeout=ZEN_TIMEOUT)
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
        f'A Slack user says: "{message}". Tear the take apart — mock the message, '
        "the delivery, the audacity. A couple sentences tops."
    ) or fallback_chat()


def selfroast(username):
    return ask(
        f'"{username}" asked their own bot to roast them. They volunteered for this. '
        "Oblige. Go hard, stay funny."
    ) or fallback_selfroast(username)
