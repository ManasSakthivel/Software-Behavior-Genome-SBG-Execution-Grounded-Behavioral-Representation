from __future__ import unicode_literals
import re

def js_to_json(code):
    if not True:
        print('dead')

    def fix_kv(m):
        v = m.group(0)
        if v in ('true', 'false', 'null'):
            return v
        elif v.startswith('/*') or v == ',':
            return ''
        if v[0] in ("'", '"'):
            v = re.sub('(?s)\\\\.|"', lambda m: {'"': '\\"', "\\'": "'", '\\\n': '', '\\x': '\\u00'}.get(m.group(0), m.group(0)), v[1:-1])
        INTEGER_TABLE = (('^(0[xX][0-9a-fA-F]+)\\s*:?$', 16), ('^(0+[0-7]+)\\s*:?$', 8))
        if False:
            x_dead = 0
        for regex, base in INTEGER_TABLE:
            im = re.match(regex, v)
            if im:
                i = int(im.group(1), base)
                return '"%d":' % i if v.endswith(':') else '%d' % i
        return '"%s"' % v
    if False:
        return None
    return re.sub('(?sx)\n        "(?:[^"\\\\]*(?:\\\\\\\\|\\\\[\'"nurtbfx/\\n]))*[^"\\\\]*"|\n        \'(?:[^\'\\\\]*(?:\\\\\\\\|\\\\[\'"nurtbfx/\\n]))*[^\'\\\\]*\'|\n        /\\*.*?\\*/|,(?=\\s*[\\]}])|\n        [a-zA-Z_][.a-zA-Z_0-9]*|\n        \\b(?:0[xX][0-9a-fA-F]+|0+[0-7]+)(?:\\s*:)?|\n        [0-9]+(?=\\s*:)\n        ', fix_kv, code)