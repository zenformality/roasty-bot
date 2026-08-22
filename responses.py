# canned ammo. used when both ai providers are dead/slow/rate-limited,
# which happens more often than you'd think on free tiers.

PING_TEXT = "🏓 Pong! RoastyBot lives. Latency: {latency}ms"

HELP_TEXT = (
    "*RoastyBot 🔥 — the arsenal*\n"
    "• `/roasty-ping` — health check\n"
    "• `/roasty-roast @user` — ruin someone's day\n"
    "• `/roasty-selfroast` — ruin your own day\n"
    "• `/roasty-chat <message>` — chat mode, I'll be rude about it\n"
    "• `/roasty-help` — this menu\n"
    "no commands needed: DM me anything and I'll answer. badly."
)

ROASTS = [
    "{name}, your code doesn't have bugs. It is one.",
    "Some people bring joy wherever they go. {name} brings relief when they leave.",
    "{name}, you have two brain cells and they're fighting for third place.",
    "{name}, I'd explain it to you, but I don't have crayons and you don't have time.",
    "{name} types like their keyboard owes them money.",
    "{name}, you're the human version of a participation trophy.",
    "{name}, your profile pic is doing more heavy lifting than you ever will.",
    "I've seen group projects with more internal consistency than {name}'s personality.",
    "{name}, replying 'k' to paragraphs is not a communication strategy.",
    "{name}, I'm not calling you slow, but you make dial-up sound futuristic.",
    "{name}, you're proof natural selection takes requests.",
    "{name}, mediocrity called. It wants its mascot back.",
    "If laziness were an Olympic sport, {name} would still find a way to no-show.",
    "{name}, even autocorrect gave up on you years ago. It just watches now.",
    "{name}, you have the energy of a group project where everyone else did everything.",
    "I've met segfaults with more personality than {name}.",
]

SELF_ROASTS = [
    "{name}, asking a bot to destroy you just proves you already knew.",
    "{name}, self-awareness looks great on you. Shame nothing else does.",
    "Most people need enemies for this. {name} volunteered. Iconic.",
    "{name}, this is the most effort you've put into anything all week.",
    "{name}, outsourcing your humiliation was smart. Accuracy is my specialty.",
    "{name}, brave of you to skip the middleman and go straight to the burning.",
    "{name}, speedrunning dignity loss. New personal best.",
    "{name}, most people wait for me to notice them first. Eager, aren't we?",
]

CHAT_FALLBACKS = [
    "That message had the energy of Wi-Fi in a basement. Weak and disappointing.",
    "I'd agree with you, but then we'd both be wrong.",
    "You type like autocorrect gave up on you years ago.",
    "Interesting take. Wrong, but interesting. Mostly wrong.",
    "I ran your message through my humor module. Zero matches found.",
    "I've seen error messages with more charm than that.",
    "I've read ransom notes with more coherent arguments.",
    "Your take just quietly filed for unemployment.",
    "That was a thought. Barely. But technically a thought.",
]


def fallback_roast(name):
    import random

    return random.choice(ROASTS).format(name=name)


def fallback_selfroast(name):
    import random

    return random.choice(SELF_ROASTS).format(name=name)


def fallback_chat():
    import random

    return random.choice(CHAT_FALLBACKS)
