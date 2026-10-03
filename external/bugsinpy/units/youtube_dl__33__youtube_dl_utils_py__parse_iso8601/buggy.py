# BugsInPy youtube-dl/33 | https://github.com/ytdl-org/youtube-dl | youtube_dl/utils.py | unit parse_iso8601
# license: Unlicense (upstream project); extracted verbatim, closure only, no edits
# commit 50c8266ef0b2b6d011257a909f47fd623dda8eb2 (buggy)
import calendar

import datetime

import re

def parse_iso8601(date_str, delimiter='T'):
    """ Return a UNIX timestamp from the given date """

    if date_str is None:
        return None

    m = re.search(
        r'Z$| ?(?P<sign>\+|-)(?P<hours>[0-9]{2}):?(?P<minutes>[0-9]{2})$',
        date_str)
    if not m:
        timezone = datetime.timedelta()
    else:
        date_str = date_str[:-len(m.group(0))]
        if not m.group('sign'):
            timezone = datetime.timedelta()
        else:
            sign = 1 if m.group('sign') == '+' else -1
            timezone = datetime.timedelta(
                hours=sign * int(m.group('hours')),
                minutes=sign * int(m.group('minutes')))
    date_format =  '%Y-%m-%d{0}%H:%M:%S'.format(delimiter)
    dt = datetime.datetime.strptime(date_str, date_format) - timezone
    return calendar.timegm(dt.timetuple())
