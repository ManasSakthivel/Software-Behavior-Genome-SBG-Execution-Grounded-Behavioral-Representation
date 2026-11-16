# BugsInPy youtube-dl/32 | https://github.com/ytdl-org/youtube-dl | youtube_dl/utils.py | unit strip_jsonp
# license: Unlicense (upstream project); extracted verbatim, closure only, no edits
# commit bf951c5e29548cfed80480389762edd29fcc8825 (buggy)
from __future__ import unicode_literals

import re

def strip_jsonp(code):
    return re.sub(r'(?s)^[a-zA-Z0-9_]+\s*\(\s*(.*)\);?\s*?\s*$', r'\1', code)
