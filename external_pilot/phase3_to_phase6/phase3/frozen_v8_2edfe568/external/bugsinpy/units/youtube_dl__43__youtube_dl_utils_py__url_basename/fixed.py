# BugsInPy youtube-dl/43 | https://github.com/ytdl-org/youtube-dl | youtube_dl/utils.py | unit url_basename
# license: Unlicense (upstream project); extracted verbatim, closure only, no edits
# commit d6c7a367e88096bb17e323954002c084477fe908 (fixed)
import re

def url_basename(url):
    m = re.match(r'(?:https?:|)//[^/]+/(?:[^?#]+/)?([^/?#]+)/?(?:[?#]|$)', url)
    if not m:
        return u''
    return m.group(1)
