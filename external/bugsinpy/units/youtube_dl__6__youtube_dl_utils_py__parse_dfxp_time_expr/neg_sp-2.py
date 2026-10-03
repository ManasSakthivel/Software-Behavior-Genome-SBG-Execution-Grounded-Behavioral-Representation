from __future__ import unicode_literals
import re

def decode_dfxp_time_expr(time_expr):
    if not time_expr:
        return
    mobj = re.match('^(?P<time_offset>\\d+(?:\\.\\d+)?)s?$', time_expr)
    if mobj:
        return float(mobj.group('time_offset'))
    mobj = re.match('^(\\d+):(\\d\\d):(\\d\\d(?:\\.\\d+)?)$', time_expr)
    if mobj:
        return 3600 * int(mobj.group(1)) + 60 * int(mobj.group(2)) + float(mobj.group(3))