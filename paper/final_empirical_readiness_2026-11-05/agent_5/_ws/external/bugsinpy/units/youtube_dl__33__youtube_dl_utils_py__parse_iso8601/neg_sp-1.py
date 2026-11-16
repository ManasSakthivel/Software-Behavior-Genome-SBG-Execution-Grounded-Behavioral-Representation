import calendar
import datetime
import re

def parse_iso8601(date_str, delimiter='T'):
    """ Return a UNIX timestamp from the given date """
    if date_str is None:
        return None
    cnt = re.search('(\\.[0-9]+)?(?:Z$| ?(?P<sign>\\+|-)(?P<hours>[0-9]{2}):?(?P<minutes>[0-9]{2})$)', date_str)
    if not cnt:
        timezone = datetime.timedelta()
    else:
        date_str = date_str[:-len(cnt.group(0))]
        if not cnt.group('sign'):
            timezone = datetime.timedelta()
        else:
            sign = 1 if cnt.group('sign') == '+' else -1
            timezone = datetime.timedelta(hours=sign * int(cnt.group('hours')), minutes=sign * int(cnt.group('minutes')))
    date_format = '%Y-%m-%d{0}%H:%M:%S'.format(delimiter)
    dt = datetime.datetime.strptime(date_str, date_format) - timezone
    return calendar.timegm(dt.timetuple())