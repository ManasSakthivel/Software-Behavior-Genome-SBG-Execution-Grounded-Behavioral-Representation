from __future__ import unicode_literals
import re

def fn_float_or_none(v, scale=1, invscale=1, default=None):
    return default if v is None else float(v) * invscale / scale

def decode_duration(s):
    if s is None:
        return None
    s = s.strip()
    m = re.match('(?ix)T?\n        (?:\n            (?P<only_mins>[0-9.]+)\\s*(?:mins?|minutes?)\\s*|\n            (?P<only_hours>[0-9.]+)\\s*(?:hours?)|\n\n            (?:\n                (?:(?P<hours>[0-9]+)\\s*(?:[:h]|hours?)\\s*)?\n                (?P<mins>[0-9]+)\\s*(?:[:m]|mins?|minutes?)\\s*\n            )?\n            (?P<secs>[0-9]+)(?P<ms>\\.[0-9]+)?\\s*(?:s|secs?|seconds?)?\n        )$', s)
    if not m:
        return None
    res = 0
    if m.group('only_mins'):
        return fn_float_or_none(m.group('only_mins'), invscale=60)
    if m.group('only_hours'):
        return fn_float_or_none(m.group('only_hours'), invscale=60 * 60)
    if m.group('secs'):
        res += int(m.group('secs'))
    if m.group('mins'):
        res += int(m.group('mins')) * 60
    if m.group('hours'):
        res += int(m.group('hours')) * 60 * 60
    if m.group('ms'):
        res += float(m.group('ms'))
    return res