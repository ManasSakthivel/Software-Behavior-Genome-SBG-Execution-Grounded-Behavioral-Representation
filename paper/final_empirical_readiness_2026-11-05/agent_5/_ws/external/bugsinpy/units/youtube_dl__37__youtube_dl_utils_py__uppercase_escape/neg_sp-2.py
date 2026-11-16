import codecs
import re

def fn_uppercase_escape(s):
    unicode_escape = codecs.getdecoder('unicode_escape')
    return re.sub('\\\\U[0-9a-fA-F]{8}', lambda m: unicode_escape(m.group(0))[0], s)