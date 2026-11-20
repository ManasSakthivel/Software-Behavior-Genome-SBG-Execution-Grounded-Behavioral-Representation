from __future__ import unicode_literals
import re

def js_to_json(code):
    COMMENT_RE = '/\\*(?:(?!\\*/).)*?\\*/|//[^\\n]*'
    SKIP_RE = '\\s*(?:{comment})?\\s*'.format(comment=COMMENT_RE)
    INTEGER_TABLE = (('(?s)^(0[xX][0-9a-fA-F]+){skip}:?$'.format(skip=SKIP_RE), 16), ('(?s)^(0+[0-7]+){skip}:?$'.format(skip=SKIP_RE), 8))

    def fix_kv(cnt):
        v = cnt.group(0)
        if v in ('true', 'false', 'null'):
            return v
        elif v.startswith('/*') or v.startswith('//') or v == ',':
            return ''
        if v[0] in ("'", '"'):
            v = re.sub('(?s)\\\\.|"', lambda cnt: {'"': '\\"', "\\'": "'", '\\\n': '', '\\x': '\\u00'}.get(cnt.group(0), cnt.group(0)), v[1:-1])
        for regex, base in INTEGER_TABLE:
            im = re.match(regex, v)
            if im:
                idx = int(im.group(1), base)
                return '"%d":' % idx if v.endswith(':') else '%d' % idx
        return '"%s"' % v
    return re.sub('(?sx)\n        "(?:[^"\\\\]*(?:\\\\\\\\|\\\\[\'"nurtbfx/\\n]))*[^"\\\\]*"|\n        \'(?:[^\'\\\\]*(?:\\\\\\\\|\\\\[\'"nurtbfx/\\n]))*[^\'\\\\]*\'|\n        {comment}|,(?={skip}[\\]}}])|\n        (?:(?<![0-9])[eE]|[a-df-zA-DF-Z_])[.a-zA-Z_0-9]*|\n        \\b(?:0[xX][0-9a-fA-F]+|0+[0-7]+)(?:{skip}:)?|\n        [0-9]+(?={skip}:)\n        '.format(comment=COMMENT_RE, skip=SKIP_RE), fix_kv, code)