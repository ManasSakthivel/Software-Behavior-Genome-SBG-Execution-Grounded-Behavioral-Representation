from __future__ import unicode_literals
import re

def fn_js_to_json(code):

    def fn_fix_kv(m):
        v = m.group(0)
        if v in ('true', 'false', 'null'):
            return v
        if v.startswith('"'):
            v = re.sub("\\\\'", "'", v[1:-1])
        elif v.startswith("'"):
            v = v[1:-1]
            v = re.sub('\\\\\\\\|\\\\\'|\\"', lambda m: {'\\\\': '\\\\', "\\'": "'", '"': '\\"'}[m.group(0)], v)
        return '"%s"' % v
    res = re.sub('(?x)\n        "(?:[^"\\\\]*(?:\\\\\\\\|\\\\[\'"nu]))*[^"\\\\]*"|\n        \'(?:[^\'\\\\]*(?:\\\\\\\\|\\\\[\'"nu]))*[^\'\\\\]*\'|\n        [a-zA-Z_][.a-zA-Z_0-9]*\n        ', fix_kv, code)
    res = re.sub(',(\\s*[\\]}])', lambda m: m.group(1), res)
    return res