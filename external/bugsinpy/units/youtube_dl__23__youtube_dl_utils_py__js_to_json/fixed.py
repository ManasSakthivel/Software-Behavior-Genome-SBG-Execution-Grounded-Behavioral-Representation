# BugsInPy youtube-dl/23 | https://github.com/ytdl-org/youtube-dl | youtube_dl/utils.py | unit js_to_json
# license: Unlicense (upstream project); extracted verbatim, closure only, no edits
# commit b3ee552e4b918fb720111b23147e24fa5475a74b (fixed)
from __future__ import unicode_literals

import re

def js_to_json(code):
    def fix_kv(m):
        v = m.group(0)
        if v in ('true', 'false', 'null'):
            return v
        elif v.startswith('/*') or v.startswith('//') or v == ',':
            return ""

        if v[0] in ("'", '"'):
            v = re.sub(r'(?s)\\.|"', lambda m: {
                '"': '\\"',
                "\\'": "'",
                '\\\n': '',
                '\\x': '\\u00',
            }.get(m.group(0), m.group(0)), v[1:-1])

        INTEGER_TABLE = (
            (r'^(0[xX][0-9a-fA-F]+)\s*:?$', 16),
            (r'^(0+[0-7]+)\s*:?$', 8),
        )

        for regex, base in INTEGER_TABLE:
            im = re.match(regex, v)
            if im:
                i = int(im.group(1), base)
                return '"%d":' % i if v.endswith(':') else '%d' % i

        return '"%s"' % v

    return re.sub(r'''(?sx)
        "(?:[^"\\]*(?:\\\\|\\['"nurtbfx/\n]))*[^"\\]*"|
        '(?:[^'\\]*(?:\\\\|\\['"nurtbfx/\n]))*[^'\\]*'|
        /\*.*?\*/|//[^\n]*|,(?=\s*[\]}])|
        [a-zA-Z_][.a-zA-Z_0-9]*|
        \b(?:0[xX][0-9a-fA-F]+|0+[0-7]+)(?:\s*:)?|
        [0-9]+(?=\s*:)
        ''', fix_kv, code)
