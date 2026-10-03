# BugsInPy youtube-dl/37 | https://github.com/ytdl-org/youtube-dl | youtube_dl/utils.py | unit uppercase_escape
# license: Unlicense (upstream project); extracted verbatim, closure only, no edits
# commit 98b7cf1acefe398f792ca6ff4c5f84f1b7785fcb (buggy)
import re

def uppercase_escape(s):
    return re.sub(
        r'\\U[0-9a-fA-F]{8}',
        lambda m: m.group(0).decode('unicode-escape'), s)
