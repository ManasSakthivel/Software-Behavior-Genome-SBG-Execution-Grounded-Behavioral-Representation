# BugsInPy spacy/1 | https://github.com/explosion/spaCy | spacy/errors.py | unit add_codes
# license: MIT (upstream project); extracted verbatim, closure only, no edits
# commit 9ce059dd067ecc3f097d04023e3cfa0d70d35bb8 (buggy)
from __future__ import unicode_literals

def add_codes(err_cls):
    """Add error codes to string messages via class attribute names."""

    class ErrorsWithCodes(object):
        def __getattribute__(self, code):
            msg = getattr(err_cls, code)
            return "[{code}] {msg}".format(code=code, msg=msg)

    return ErrorsWithCodes()
