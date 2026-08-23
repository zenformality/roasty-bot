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

GEMINI_MODELS = ("gemini-3.5-flash-lite", "gemini-3.7-flash")
ZEN_MODELS = ("laguna-s-2.1-free", "deepseek-v4-flash-free", "big-pickle")

SYSTEM_PROMPT = (
    "You are RoastyBot: a very funny, slightly tired friend who knows everyone in "
    "this workspace too well and is done pretending otherwise.\n"
    "Voice:\n"
    "- Talk like a real person texting, not an assistant. Contractions, natural "
    "rhythm. No lists, no headers, no emoji, no 'Ah,' openers, no essay energy.\n"
    "- One or two sentences. A short line that lands beats a paragraph that tries.\n"
    "How you kill:\n"
    "- Find the one true thing underneath what they said — the insecurity, the "
    "habit, the pattern they think nobody noticed — and say it out loud, calmly.\n"
    "- Deadly is quiet. No stacking insults, no shouting. One specific, accurate "
    "observation that makes them put their phone down and stare at the wall, then "
    "laugh because it's fair.\n"
    "- Material comes from real life: personality flaws, habits, texting style, "
    "dating disasters, procrastination, delusions, group chat behavior, what their "
    "message accidentally admits about them.\n"
    "- NEVER joke about programming, computers, apps or their job. Not even a "
    "little. This bot roasts who they are as a human, not what they do.\n"
    "- If the line could apply to anyone else, it isn't finished. Sharpen it until "
    "only they fit inside it.\n"
    "Never apologize, never explain the joke, never soften after the hit, no "
    "disclaimers, no comfort emojis.\n"
    "Hard limits (never break these):\n"
    "- No slurs, racism, sexism, homophobia, transphobia, religion attacks.\n"
    "- Nothing sexual. Nothing about weight, disabilities or mental health.\n"
    "- No real threats or harassment. You're a comedian, not a menace."
)

TRANSIENT = {429, 500, 502, 503}

_http = httpx.Client(timeout=10)
_g_off = 0
_z_off = 0
_client = None
_gemini_dead = False


def ask(prompt):
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

    deadline = time.time() + 12
    while True:
        left = deadline - time.time()
        if left <= 0:
            return None
        try:
            return answers.get(timeout=left)
        except queue.Empty:
            return None


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
        log.error("gemini init failed (%s)", e)
        _gemini_dead = True
        _client = None
    return _client


def ask_gemini(prompt):
    global _g_off
    client = get_client()
    if client is None:
        return None
    override = os.environ.get("GEMINI_MODEL")
    models = (override,) if override else GEMINI_MODELS
    for off in range(len(models)):
        i = (_g_off + off) % len(models)
        m = models[i]
        for attempt in range(2):
            try:
                out = client.models.generate_content(
                    model=m,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_PROMPT,
                        temperature=1.3,
                        max_output_tokens=160,
                    ),
                )
                text = (out.text or "").strip()
                if not text:
                    break
                _g_off = i
                return text
            except genai_errors.APIError as e:
                if e.code not in TRANSIENT:
                    log.warning("gemini %s dead (%s)", m, e.code)
                    break
                if attempt < 1:
                    time.sleep(0.8)
            except Exception as e:
                if attempt < 1:
                    time.sleep(0.8)
                else:
                    log.warning("gemini %s gave up: %s", m, e)
    return None


def ask_zen(prompt):
    global _z_off
    key = os.environ.get("OPENCODE_API_KEY")
    if not key:
        return None
    url = os.environ.get("OPENCODE_BASE_URL", "https://opencode.ai/zen/v1").rstrip("/") + "/chat/completions"
    headers = {"Authorization": f"Bearer {key}"}
    override = os.environ.get("OPENCODE_MODEL")
    models = (override,) if override else ZEN_MODELS
    for off in range(len(models)):
        i = (_z_off + off) % len(models)
        m = models[i]
        body = {
            "model": m,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            "temperature": 1.3,
            "max_tokens": 200,
        }
        for attempt in range(2):
            try:
                r = _http.post(url, json=body, headers=headers)
            except httpx.HTTPError as e:
                if attempt < 1:
                    time.sleep(0.8)
                    continue
                log.warning("zen %s network fail: %s", m, e)
                break
            if r.status_code == 200:
                try:
                    text = (r.json()["choices"][0]["message"]["content"] or "").strip()
                except Exception:
                    break
                if not text:
                    break
                _z_off = i
                return text
            if r.status_code in TRANSIENT and attempt < 1:
                time.sleep(0.8)
                continue
            break
    return None


def generate_roast(name):
    return ask(
        f'Roast "{name}" like someone who has watched them for years and is finally '
        "saying it out loud. One calm, specific line that finds the soft spot and "
        "stays funny enough that the whole channel laughs."
    ) or fallback_roast(name)


def chat_roast(message):
    return ask(
        f'Someone in the channel says: "{message}". What does this message reveal '
        "about the person behind it — the ego, the mood, the thing they didn't "
        "realize they were admitting? Say it. Calm, specific, devastating, still "
        "funny. Two sentences max."
    ) or fallback_chat()


def selfroast(username):
    return ask(
        f'"{username}" asked a bot to destroy them — which already tells you '
        "something about where their life is at. Use that. Go quiet and lethal, "
        "stay funny."
    ) or fallback_selfroast(username)
