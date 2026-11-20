import datetime
import email.utils
import re

def unified_strdate(date_str):
    if date_str is None:
        return None
    upload_date = None
    date_str = date_str.replace(',', ' ')
    date_str = re.sub(' ?(\\+|-)[0-9]{2}:?[0-9]{2}$', '', date_str)
    format_expressions = ['%d %B %Y', '%d %b %Y', '%B %d %Y', '%b %d %Y', '%b %dst %Y %I:%M%p', '%b %dnd %Y %I:%M%p', '%b %dth %Y %I:%M%p', '%Y-%m-%d', '%Y/%m/%d', '%d.%m.%Y', '%d/%m/%Y', '%d/%m/%y', '%Y/%m/%d %H:%M:%S', '%d/%m/%Y %H:%M:%S', '%Y-%m-%d %H:%M:%S', '%d.%m.%Y %H:%M', '%d.%m.%Y %H.%M', '%Y-%m-%dT%H:%M:%SZ', '%Y-%m-%dT%H:%M:%S.%fZ', '%Y-%m-%dT%H:%M:%S.%f0Z', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M:%S.%f', '%Y-%m-%dT%H:%M']
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