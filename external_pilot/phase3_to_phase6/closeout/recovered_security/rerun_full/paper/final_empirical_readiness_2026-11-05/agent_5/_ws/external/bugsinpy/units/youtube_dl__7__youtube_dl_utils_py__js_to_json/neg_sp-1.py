from __future__ import unicode_literals
import re

def js_to_json(code):

    def fix_kv(cnt):
        v = cnt.group(0)
        if v in ('true', 'false', 'null'):
            return v
        if v.startswith('"'):
            v = re.sub("\\\\'", "'", v[1:-1])
        elif v.startswith("'"):
            v = v[1:-1]
            v = re.sub('\\\\\\\\|\\\\\'|\\"', lambda cnt: {'\\\\': '\\\\', "\\'": "'", '"': '\\"'}[cnt.group(0)], v)
        return '"%s"' % v
    out = re.sub('(?x)\n        "(?:[^"\\\\]*(?:\\\\\\\\|\\\\[\'"nu]))*[^"\\\\]*"|\n        \'(?:[^\'\\\\]*(?:\\\\\\\\|\\\\[\'"nu]))*[^\'\\\\]*\'|\n        [a-zA-Z_][.a-zA-Z_0-9]*\n        ', fix_kv, code)
    out = re.sub(',(\\s*[\\]}])', lambda cnt: cnt.group(1), out)
    return out