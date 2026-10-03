# BugsInPy youtube-dl/10 | https://github.com/ytdl-org/youtube-dl | youtube_dl/utils.py | unit js_to_json
# license: Unlicense (upstream project); extracted verbatim, closure only, no edits
# commit d305dd73a3d6927f0a2c63d08662a183fa173833 (fixed)
from __future__ import unicode_literals

import re

def js_to_json(code):
    def fix_kv(m):
        v = m.group(0)
        if v in ('true', 'false', 'null'):
            return v
        if v.startswith('"'):
            return v
        if v.startswith("'"):
            v = v[1:-1]
            v = re.sub(r"\\\\|\\'|\"", lambda m: {
                '\\\\': '\\\\',
                "\\'": "'",
                '"': '\\"',
            }[m.group(0)], v)
        return '"%s"' % v

    res = re.sub(r'''(?x)
        "(?:[^"\\]*(?:\\\\|\\['"nu]))*[^"\\]*"|
        '(?:[^'\\]*(?:\\\\|\\['"nu]))*[^'\\]*'|
        [a-zA-Z_][.a-zA-Z_0-9]*
        ''', fix_kv, code)
    res = re.sub(r',(\s*\])', lambda m: m.group(1), res)
    return res
