from __future__ import unicode_literals
import re

def fn_strip_jsonp(code):
    return re.sub('(?s)^[a-zA-Z0-9_]+\\s*\\(\\s*(.*)\\);?\\s*?(?://[^\\n]*)*$', '\\1', code)