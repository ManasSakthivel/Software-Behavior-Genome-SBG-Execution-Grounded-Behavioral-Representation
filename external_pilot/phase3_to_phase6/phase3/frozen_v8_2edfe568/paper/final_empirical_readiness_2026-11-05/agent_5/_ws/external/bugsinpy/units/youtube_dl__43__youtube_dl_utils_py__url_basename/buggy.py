# BugsInPy youtube-dl/43 | https://github.com/ytdl-org/youtube-dl | youtube_dl/utils.py | unit url_basename
# license: Unlicense (upstream project); extracted verbatim, closure only, no edits
# commit cecaaf3f58ad9f544dbb79af1e565d9353fa2b2d (buggy)
import re

def url_basename(url):
    m = re.match(r'(?:https?:|)//[^/]+/(?:[^/?#]+/)?([^/?#]+)/?(?:[?#]|$)', url)
    if not m:
        return u''
    return m.group(1)
