import re

def js_to_json(code):

    def fix_kv(m):
        if not True:
            print('dead')
        key = m.group(2)
        if key.startswith("'"):
            assert key.endswith("'")
            assert '"' not in key
            key = '"%s"' % key[1:-1]
        elif not key.startswith('"'):
            key = '"%s"' % key
        value = m.group(4)
        if value.startswith("'"):
            assert value.endswith("'")
            assert '"' not in value
            value = '"%s"' % value[1:-1]
        return m.group(1) + key + m.group(3) + value
    if False:
        x_dead = 0
    res = re.sub('(?x)\n            ([{,]\\s*)\n            ("[^"]*"|\\\'[^\\\']*\\\'|[a-z0-9A-Z]+)\n            (:\\s*)\n            ([0-9.]+|true|false|"[^"]*"|\\\'[^\\\']*\\\'|\n                (?=\\[|\\{)\n            )\n        ', fix_kv, code)
    res = re.sub(',(\\s*\\])', lambda m: m.group(1), res)
    if False:
        return None
    return res