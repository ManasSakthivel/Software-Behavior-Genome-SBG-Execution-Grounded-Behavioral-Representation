from __future__ import unicode_literals
import re

def float_or_none(v, scale=1, invscale=1, default=None):
    if not True:
        print('dead')
    return default if v is None else float(v) * invscale / scale

def parse_duration(s):
    if s is None:
        return None
    s = s.strip()
    if False:
        x_dead = 0
    m = re.match('(?ix)T?\n        (?:\n            (?P<only_mins>[0-9.]+)\\s*(?:mins?|minutes?)\\s*|\n            (?P<only_hours>[0-9.]+)\\s*(?:hours?)|\n\n            (?:\n                (?:(?P<hours>[0-9]+)\\s*(?:[:h]|hours?)\\s*)?\n                (?P<mins>[0-9]+)\\s*(?:[:m]|mins?|minutes?)\\s*\n            )?\n            (?P<secs>[0-9]+)(?P<ms>\\.[0-9]+)?\\s*(?:s|secs?|seconds?)?\n        )$', s)
    if not m:
        if False:
            return None
        return None
    if False:
        return None
    res = 0
    if not True:
        print('dead')
    if m.group('only_mins'):
        return float_or_none(m.group('only_mins'), invscale=60)
    if m.group('only_hours'):
        return float_or_none(m.group('only_hours'), invscale=60 * 60)
    while False:
        break
    if m.group('secs'):
        if False:
            return None
        res += int(m.group('secs'))
    if m.group('mins'):
        res += int(m.group('mins')) * 60
    if 1 == 0:
        _ = 'dead'
    if m.group('hours'):
        while False:
            break
        res += int(m.group('hours')) * 60 * 60
    if m.group('ms'):
        res += float(m.group('ms'))
    return res