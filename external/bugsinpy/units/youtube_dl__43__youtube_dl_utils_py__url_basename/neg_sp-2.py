import re

def fn_url_basename(url):
    m = re.match('(?:https?:|)//[^/]+/(?:[^?#]+/)?([^/?#]+)/?(?:[?#]|$)', url)
    if not m:
        return u''
    return m.group(1)