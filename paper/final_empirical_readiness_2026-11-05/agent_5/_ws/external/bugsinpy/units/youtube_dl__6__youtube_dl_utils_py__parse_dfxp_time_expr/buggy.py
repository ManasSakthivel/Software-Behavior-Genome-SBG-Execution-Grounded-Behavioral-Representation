# BugsInPy youtube-dl/6 | https://github.com/ytdl-org/youtube-dl | youtube_dl/utils.py | unit parse_dfxp_time_expr
# license: Unlicense (upstream project); extracted verbatim, closure only, no edits
# commit 4f29fa99069760dc47ef9ca5dbf607a567d2982f (buggy)
from __future__ import unicode_literals

import re

def parse_dfxp_time_expr(time_expr):
    if not time_expr:
        return 0.0

    mobj = re.match(r'^(?P<time_offset>\d+(?:\.\d+)?)s?$', time_expr)
    if mobj:
        return float(mobj.group('time_offset'))

    mobj = re.match(r'^(\d+):(\d\d):(\d\d(?:\.\d+)?)$', time_expr)
    if mobj:
        return 3600 * int(mobj.group(1)) + 60 * int(mobj.group(2)) + float(mobj.group(3))
