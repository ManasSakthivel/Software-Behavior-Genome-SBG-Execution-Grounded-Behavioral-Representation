# BugsInPy youtube-dl/31 | https://github.com/ytdl-org/youtube-dl | youtube_dl/utils.py | unit parse_duration
# license: Unlicense (upstream project); extracted verbatim, closure only, no edits
# commit ab07963b5cc79812c6fb7e4f9e363533d8123830 (buggy)
from __future__ import unicode_literals

import re

def parse_duration(s):
    if s is None:
        return None

    s = s.strip()

    m = re.match(
        r'''(?ix)T?
            (?:
                (?:(?P<hours>[0-9]+)\s*(?:[:h]|hours?)\s*)?
                (?P<mins>[0-9]+)\s*(?:[:m]|mins?|minutes?)\s*
            )?
            (?P<secs>[0-9]+)(?P<ms>\.[0-9]+)?\s*(?:s|secs?|seconds?)?$''', s)
    if not m:
        return None
    res = int(m.group('secs'))
    if m.group('mins'):
        res += int(m.group('mins')) * 60
        if m.group('hours'):
            res += int(m.group('hours')) * 60 * 60
    if m.group('ms'):
        res += float(m.group('ms'))
    return res
