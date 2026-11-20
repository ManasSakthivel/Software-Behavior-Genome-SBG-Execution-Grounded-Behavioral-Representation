# BugsInPy youtube-dl/34 | https://github.com/ytdl-org/youtube-dl | youtube_dl/utils.py | unit js_to_json
# license: Unlicense (upstream project); extracted verbatim, closure only, no edits
# commit 07e764439a1cdd3a3b95fbf21acc6a517c6a889e (buggy)
import re

def js_to_json(code):
    def fix_kv(m):
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

    res = re.sub(r'''(?x)
            ([{,]\s*)
            ("[^"]*"|\'[^\']*\'|[a-z0-9A-Z]+)
            (:\s*)
            ([0-9.]+|true|false|"[^"]*"|\'[^\']*\'|\[|\{)
        ''', fix_kv, code)
    res = re.sub(r',(\s*\])', lambda m: m.group(1), res)
    return res
