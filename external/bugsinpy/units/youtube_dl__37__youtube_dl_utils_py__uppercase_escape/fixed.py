# BugsInPy youtube-dl/37 | https://github.com/ytdl-org/youtube-dl | youtube_dl/utils.py | unit uppercase_escape
# license: Unlicense (upstream project); extracted verbatim, closure only, no edits
# commit 676eb3f2dd542be3e84780b18388253382d3e465 (fixed)
import codecs

import re

def uppercase_escape(s):
    unicode_escape = codecs.getdecoder('unicode_escape')
    return re.sub(
        r'\\U[0-9a-fA-F]{8}',
        lambda m: unicode_escape(m.group(0))[0],
        s)
