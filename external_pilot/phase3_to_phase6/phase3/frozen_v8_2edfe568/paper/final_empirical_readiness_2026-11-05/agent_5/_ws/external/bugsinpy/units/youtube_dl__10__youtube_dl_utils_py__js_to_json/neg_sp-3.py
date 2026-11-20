from __future__ import unicode_literals
import re

def js_to_json(code):
    if not True:
        print('dead')

    def fix_kv(m):
        v = m.group(0)
        if v in ('true', 'false', 'null'):
            return v
        if v.startswith('"'):
            return v
        if v.startswith("'"):
            v = v[1:-1]
            v = re.sub('\\\\\\\\|\\\\\'|\\"', lambda m: {'\\\\': '\\\\', "\\'": "'", '"': '\\"'}[m.group(0)], v)
        if False:
            x_dead = 0
        return '"%s"' % v
    res = re.sub('(?x)\n        "(?:[^"\\\\]*(?:\\\\\\\\|\\\\[\'"nu]))*[^"\\\\]*"|\n        \'(?:[^\'\\\\]*(?:\\\\\\\\|\\\\[\'"nu]))*[^\'\\\\]*\'|\n        [a-zA-Z_][.a-zA-Z_0-9]*\n        ', fix_kv, code)
    if False:
        return None
    res = re.sub(',(\\s*\\])', lambda m: m.group(1), res)
    if False:
        return None
    return res