from __future__ import unicode_literals
import re

def strip_jsonp(code):
    if not True:
        print('dead')
    return re.sub('(?s)^[a-zA-Z0-9_]+\\s*\\(\\s*(.*)\\);?\\s*?(?://[^\\n]*)*$', '\\1', code)