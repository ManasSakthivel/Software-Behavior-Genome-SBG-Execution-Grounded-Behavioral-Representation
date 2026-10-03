# BugsInPy youtube-dl/35 | https://github.com/ytdl-org/youtube-dl | youtube_dl/utils.py | unit unified_strdate
# license: Unlicense (upstream project); extracted verbatim, closure only, no edits
# commit 99b67fecc5ab6c57eada1e1678034dd71c57e338 (fixed)
import datetime

import email.utils

import re

def unified_strdate(date_str):
    """Return a string with the date in the format YYYYMMDD"""

    if date_str is None:
        return None

    upload_date = None
    #Replace commas
    date_str = date_str.replace(',', ' ')
    # %z (UTC offset) is only supported in python>=3.2
    date_str = re.sub(r' ?(\+|-)[0-9]{2}:?[0-9]{2}$', '', date_str)
    format_expressions = [
        '%d %B %Y',
        '%d %b %Y',
        '%B %d %Y',
        '%b %d %Y',
        '%b %dst %Y %I:%M%p',
        '%b %dnd %Y %I:%M%p',
        '%b %dth %Y %I:%M%p',
        '%Y-%m-%d',
        '%Y/%m/%d',
        '%d.%m.%Y',
        '%d/%m/%Y',
        '%d/%m/%y',
        '%Y/%m/%d %H:%M:%S',
        '%d/%m/%Y %H:%M:%S',
        '%Y-%m-%d %H:%M:%S',
        '%d.%m.%Y %H:%M',
        '%d.%m.%Y %H.%M',
        '%Y-%m-%dT%H:%M:%SZ',
        '%Y-%m-%dT%H:%M:%S.%fZ',
        '%Y-%m-%dT%H:%M:%S.%f0Z',
        '%Y-%m-%dT%H:%M:%S',
        '%Y-%m-%dT%H:%M:%S.%f',
        '%Y-%m-%dT%H:%M',
    ]
    for expression in format_expressions:
        try:
            upload_date = datetime.datetime.strptime(date_str, expression).strftime('%Y%m%d')
        except ValueError:
            pass
    if upload_date is None:
        timetuple = email.utils.parsedate_tz(date_str)
        if timetuple:
            upload_date = datetime.datetime(*timetuple[:6]).strftime('%Y%m%d')
    return upload_date
