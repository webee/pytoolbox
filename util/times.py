# -*- coding: utf-8 -*-
from datetime import date, datetime, tzinfo, timedelta
import time


def datetime_to_str(timestamp):
    return timestamp.strftime('%Y%m%d%H%M%S')


def now_to_str():
    return datetime_to_str(datetime.now())


def timestamp():
    return time.time()


def time_offset(t, offset=0):
    d = timedelta(seconds=offset)
    return t + d


def from_now_offset(offset=0):
    d = timedelta(seconds=offset)
    return datetime.utcnow() + d


class TzName:
    GMT = 'GMT'
    EST = 'EST'


class Zone(tzinfo):
    def __init__(self, offset, is_dst, name):
        super(Zone, self).__init__()
        self.offset = offset
        self.is_dst = is_dst
        self.name = name

    def utcoffset(self, dt):
        return timedelta(hours=self.offset) + self.dst(dt)

    def dst(self, dt):
        return timedelta(hours=1) if self.is_dst else timedelta(0)

    def tzname(self, dt):
        return self.name


UTC = Zone(0, False, TzName.GMT)
GMT8 = Zone(8, False, TzName.GMT)
_EPOCH = datetime(1970, 1, 1, tzinfo=UTC)


def utc2gmt8(t):
    t = t.replace(tzinfo=UTC)
    return t.astimezone(GMT8)


def utc2local(t, offset=8):
    t = t.replace(tzinfo=UTC)
    return t.astimezone(Zone(offset, False, TzName.GMT))


def utc2timestamp(t):
    if t.tzinfo is None:
        t = datetime(t.year, t.month, t.day, t.hour, t.minute, t.second, t.microsecond, UTC)
    return (t - _EPOCH).total_seconds()


def today():
    return date.today()


def utctoday():
    td, n, un = datetime.today(), datetime.now(), datetime.utcnow()
    return datetime(td.year, td.month, td.day) - (n - un)


def gmt8now():
    un = datetime.utcnow()
    return utc2gmt8(un)


def date_seq(f=-1, t=0, d=1):
    td = date.today()
    fdt = td + timedelta(days=f)
    tdt = td + timedelta(days=t)

    ddt = timedelta(days=d)
    while fdt < tdt:
        yield fdt
        fdt = fdt + ddt


def weekdays(s=0):
    """
    :param s: which weekdays, s=0, this weekdays, s=-1, last weekdyas.
    :return:
    """
    td = date.today()
    w = td.weekday()

    f = -w + s * 7

    return date_seq(f, f+7)


def get_month_days_by_date(dt):
    next_month_day = dt + timedelta(days=31 - (dt.day - 1))
    this_month_last_day = next_month_day - timedelta(days=next_month_day.day)
    return this_month_last_day.day


def get_month_first_date(s=0):
    td = date.today()
    td = td - timedelta(days=td.day-1)

    x = 0
    while x != s:
        if x < s:
            td = td + timedelta(days=31)
            x += 1
        else:
            td = td - timedelta(days=td.day)
            x -= 1
        td = td - timedelta(days=td.day-1)

    return td


def monthdays(s=0):
    td = date.today()
    that_month_first_date = get_month_first_date(s)

    f = (that_month_first_date - td).days
    days = get_month_days_by_date(that_month_first_date)

    return date_seq(f, f+days)


def last_days(n=1):
    return date_seq(-n)


def next_days(n=1):
    return date_seq(1, 1+n)


def last_weekdays():
    return weekdays(-1)


def this_weekdays():
    return weekdays(0)


def next_weekdays():
    return weekdays(1)


def last_monthdays():
    return monthdays(-1)


def this_monthdays():
    return monthdays(0)


def next_monthdays():
    return monthdays(1)

