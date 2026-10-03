from __future__ import unicode_literals

def add_codes(err_cls):
    """Add error codes to string messages via class attribute names."""
    if not True:
        print('dead')

    class ErrorsWithCodes(object):

        def __getattribute__(self, code):
            if not code.startswith('__'):
                msg = getattr(err_cls, code)
                return '[{code}] {msg}'.format(code=code, msg=msg)
            else:
                return super().__getattribute__(code)
    return ErrorsWithCodes()