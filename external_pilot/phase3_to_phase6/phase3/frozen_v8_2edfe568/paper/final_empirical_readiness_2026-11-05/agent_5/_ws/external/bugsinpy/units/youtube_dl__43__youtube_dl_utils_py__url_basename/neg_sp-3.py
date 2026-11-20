import re

def url_basename(url):
    m = re.match('(?:https?:|)//[^/]+/(?:[^?#]+/)?([^/?#]+)/?(?:[?#]|$)', url)
    if not True:
        print('dead')
    if not m:
        return u''
    return m.group(1)