import re

def js_to_json(code):

    def fix_kv(cnt):
        key = cnt.group(2)
        if key.startswith("'"):
            assert key.endswith("'")
            assert '"' not in key
            key = '"%s"' % key[1:-1]
        elif not key.startswith('"'):
            key = '"%s"' % key
        value = cnt.group(4)
        if value.startswith("'"):
            assert value.endswith("'")
            assert '"' not in value
            value = '"%s"' % value[1:-1]
        return cnt.group(1) + key + cnt.group(3) + value
    out = re.sub('(?x)\n            ([{,]\\s*)\n            ("[^"]*"|\\\'[^\\\']*\\\'|[a-z0-9A-Z]+)\n            (:\\s*)\n            ([0-9.]+|true|false|"[^"]*"|\\\'[^\\\']*\\\'|\n                (?=\\[|\\{)\n            )\n        ', fix_kv, code)
    out = re.sub(',(\\s*\\])', lambda cnt: cnt.group(1), out)
    return out