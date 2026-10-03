# BugsInPy spacy/1 | https://github.com/explosion/spaCy | spacy/errors.py | unit add_codes
# license: MIT (upstream project); extracted verbatim, closure only, no edits
# commit a987e9e45d4084f30964a4cec9914ae6ed25a73c (fixed)
from __future__ import unicode_literals

def add_codes(err_cls):
    """Add error codes to string messages via class attribute names."""

    class ErrorsWithCodes(object):
        def __getattribute__(self, code):
            if not code.startswith('__'):
                msg = getattr(err_cls, code)
                return "[{code}] {msg}".format(code=code, msg=msg)
            else:
                return super().__getattribute__(code)

    return ErrorsWithCodes()
