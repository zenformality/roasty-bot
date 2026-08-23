import random

PING_TEXT = "🏓 Pong! RoastyBot lives. Latency: {latency}ms"

HELP_TEXT = (
    "*RoastyBot 🔥 — the arsenal*\n"
    "• `/roasty-ping` — health check\n"
    "• `/roasty-roast @user` — ruin someone's day\n"
    "• `/roasty-selfroast` — ruin your own day\n"
    "• `/roasty-chat <message>` — chat mode, I'll be rude about it\n"
    "• `/roasty-help` — this menu\n"
    "no commands needed: DM me anything and I'll answer. badly.\n"
    "also: add me to a channel and I introduce myself. I drop by on my own too."
)

ROASTS = [
    "{name}, every group project you've ever been in remembers you differently than you do.",
    "{name} reads like someone who skips tutorial videos and then asks what to do.",
    "{name}, your takes arrive pre-heated from someone smarter.",
    "I'd call {name} a late bloomer but nothing's blooming.",
    "{name} has the exact energy of a printer at 4% ink that everyone's afraid to touch.",
    "{name}, your playlist explains a lot about you and none of it is flattering.",
    "if {name} had a nickel for every abandoned side project they could afford therapy. wouldn't help though.",
    "{name}, confidence: high. reasons: pending.",
    "{name} argues in circles so often GPS should sponsor them.",
    "{name}, being forgettable isn't a personality but you've committed to it anyway.",
    "{name}'s last hot take is still cooling on the windowsill of bad ideas.",
    "{name} is the friend who texts 'on my way' while still in bed.",
    "{name}, I've met NPCs with more depth.",
    "{name} peaks exclusively in arguments nobody else was having.",
    "somewhere a village is missing its idiot. it's {name}.",
    "{name}'s texts read like they're charged per letter. and per thought.",
]

SELF_ROASTS = [
    "{name} asked a bot for this. let that marinate.",
    "most people need enemies for this. {name} volunteered. respect.",
    "{name}, outsourcing your own roasting is the most efficient thing you've done all year.",
    "don't worry {name}, whatever I say, you've already said worse to yourself in the shower.",
    "{name} typed that request with their own hands. nobody made them.",
    "{name}, brave of you to cut out the middleman entirely.",
    "I'll go easy on {name}. kidding. {name}, you peaked at 'decent' and called it a career.",
    "{name} is speedrunning dignity loss. any%, no shame category.",
]

CHAT_FALLBACKS = [
    "I've read ransom notes with more coherent arguments.",
    "interesting take. wrong, but delivered with real confidence.",
    "that had the energy of airport wi-fi. technically present, doing nothing.",
    "I'd respond properly but you didn't really ask anything, did you.",
    "my humor module scanned that and returned nothing. honestly kind of impressive.",
    "you typed all of that and the best part was the send button.",
    "that was a thought. barely. but technically.",
    "error messages have said kinder things.",
    "your take just quietly filed for unemployment.",
]


def fallback_roast(name):
    return random.choice(ROASTS).format(name=name)


def fallback_selfroast(name):
    return random.choice(SELF_ROASTS).format(name=name)


def fallback_chat():
    return random.choice(CHAT_FALLBACKS)
