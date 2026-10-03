# BugsInPy youtube-dl/27 | https://github.com/ytdl-org/youtube-dl | youtube_dl/utils.py | unit parse_dfxp_time_expr
# license: Unlicense (upstream project); extracted verbatim, closure only, no edits
# commit d631d5f9f27f93767226192e4288990413fa9dbd (buggy)
from __future__ import unicode_literals

import re

def parse_dfxp_time_expr(time_expr):
    if not time_expr:
        return

    mobj = re.match(r'^(?P<time_offset>\d+(?:\.\d+)?)s?$', time_expr)
    if mobj:
        return float(mobj.group('time_offset'))

    mobj = re.match(r'^(\d+):(\d\d):(\d\d(?:\.\d+)?)$', time_expr)
    if mobj:
        return 3600 * int(mobj.group(1)) + 60 * int(mobj.group(2)) + float(mobj.group(3))
