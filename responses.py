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
    "or just @mention me anywhere. I'll find you."
)

ROASTS = [
    "{name}, your code doesn't have bugs. It is one.",
    "Some people bring joy wherever they go. {name} brings it whenever they leave.",
    "{name}, you have two brain cells and they're fighting for third place.",
    "{name}, I'd explain it to you, but I left my crayons at home.",
    "{name} types like their keyboard owes them money.",
    "{name}, you're the human version of a participation trophy.",
    "{name}, your profile pic is doing more heavy lifting than you ever will.",
    "I've seen group projects with more internal consistency than {name}'s personality.",
    "{name}, replying 'k' to paragraphs is not a communication strategy.",
    "{name}, I'm not calling you slow, but you make dial-up sound futuristic.",
]

SELF_ROASTS = [
    "{name}, asking a bot to destroy you just proves you already knew.",
    "{name}, self-awareness looks great on you. Shame nothing else does.",
    "Most people need enemies for this. {name} volunteered. Iconic.",
    "{name}, this is the most effort you've put into anything all week.",
    "{name}, outsourcing your humiliation was smart. Accuracy is my specialty.",
    "{name}, brave of you to skip the middleman and go straight to the burning.",
]

CHAT_FALLBACKS = [
    "That message had the energy of Wi-Fi in a basement. Weak and disappointing.",
    "I'd agree with you, but then we'd both be wrong.",
    "You type like autocorrect gave up on you years ago.",
    "Interesting take. Wrong, but interesting. Mostly wrong.",
    "I ran your message through my humor module. Zero matches found.",
    "I've seen error messages with more charm than that.",
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
