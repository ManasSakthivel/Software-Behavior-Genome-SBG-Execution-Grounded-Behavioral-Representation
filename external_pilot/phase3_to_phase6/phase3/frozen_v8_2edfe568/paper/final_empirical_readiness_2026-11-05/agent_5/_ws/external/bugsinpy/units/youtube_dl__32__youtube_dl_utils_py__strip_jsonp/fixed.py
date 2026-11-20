# BugsInPy youtube-dl/32 | https://github.com/ytdl-org/youtube-dl | youtube_dl/utils.py | unit strip_jsonp
# license: Unlicense (upstream project); extracted verbatim, closure only, no edits
# commit 609a61e3e6fffce3d45e845f33ae2c5fa2d432ac (fixed)
from __future__ import unicode_literals

import re

def strip_jsonp(code):
    return re.sub(
        r'(?s)^[a-zA-Z0-9_]+\s*\(\s*(.*)\);?\s*?(?://[^\n]*)*$', r'\1', code)
