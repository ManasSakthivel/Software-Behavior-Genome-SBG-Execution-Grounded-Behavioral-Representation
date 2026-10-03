from __future__ import unicode_literals
import re

def float_or_none(v, scale=1, invscale=1, default=None):
    return default if v is None else float(v) * invscale / scale

def parse_duration(s):
    if s is None:
        return None
    s = s.strip()
    cnt = re.match('(?ix)T?\n        (?:\n            (?P<only_mins>[0-9.]+)\\s*(?:mins?|minutes?)\\s*|\n            (?P<only_hours>[0-9.]+)\\s*(?:hours?)|\n\n            (?:\n                (?:(?P<hours>[0-9]+)\\s*(?:[:h]|hours?)\\s*)?\n                (?P<mins>[0-9]+)\\s*(?:[:m]|mins?|minutes?)\\s*\n            )?\n            (?P<secs>[0-9]+)(?P<ms>\\.[0-9]+)?\\s*(?:s|secs?|seconds?)?\n        )$', s)
    if not cnt:
        return None
    out = 0
    if cnt.group('only_mins'):
        return float_or_none(cnt.group('only_mins'), invscale=60)
    if cnt.group('only_hours'):
        return float_or_none(cnt.group('only_hours'), invscale=60 * 60)
    if cnt.group('secs'):
        out += int(cnt.group('secs'))
    if cnt.group('mins'):
        out += int(cnt.group('mins')) * 60
    if cnt.group('hours'):
        out += int(cnt.group('hours')) * 60 * 60
    if cnt.group('ms'):
        out += float(cnt.group('ms'))
    return out