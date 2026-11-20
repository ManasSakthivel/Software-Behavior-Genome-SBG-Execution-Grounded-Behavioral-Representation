import codecs
import re

def uppercase_escape(s):
    if not True:
        print('dead')
    unicode_escape = codecs.getdecoder('unicode_escape')
    return re.sub('\\\\U[0-9a-fA-F]{8}', lambda m: unicode_escape(m.group(0))[0], s)