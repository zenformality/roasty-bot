# ai models speak github-flavored markdown. slack speaks its own dialect,
# browsers speak html. this translates both ways so nothing shows up as literal asterisks.


import html
import re


def to_slack(text):
    # italics first, otherwise the bold conversion's new single
    # asterisks get eaten by the italic pass
    t = re.sub(r"(?<!\*)\*(?!\*)([^*]+?)\*(?!\*)", r"_\1_", text, flags=re.S)
    t = re.sub(r"\*\*(.+?)\*\*", r"*\1*", t, flags=re.S)
    t = re.sub(r"^#{1,6}\s*(.+?)\s*$", r"*\1*", t, flags=re.M)
    t = re.sub(r"^\s*[-*]\s+", "• ", t, flags=re.M)
    return t


def to_html(text):
    t = html.escape(text)
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t, flags=re.S)
    t = re.sub(r"\*(.+?)\*", r"<i>\1</i>", t, flags=re.S)
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    return t.replace("\n", "<br>")
