import re

def url_basename(url):
    cnt = re.match('(?:https?:|)//[^/]+/(?:[^?#]+/)?([^/?#]+)/?(?:[?#]|$)', url)
    if not cnt:
        return u''
    return cnt.group(1)