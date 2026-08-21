# program_id: stdlib_datetime_processor
# category: stdlib_interaction
# spec_version: 1.0

"""
Date/time processing utilities using Python's stdlib datetime module.

Spec:
  - parse_iso(s) -> datetime: parse ISO 8601 date/datetime string.
    Accepts 'YYYY-MM-DD' and 'YYYY-MM-DDTHH:MM:SS[Z]'.
    Raises ValueError for unrecognised formats.

  - business_days_between(start, end) -> int:
      Count business days (Mon-Fri) strictly between start and end dates,
      inclusive of start, exclusive of end. Returns 0 if start >= end.

  - add_business_days(date, n) -> date:
      Return the date that is n business days after `date`. n >= 0.

  - format_duration(seconds) -> str:
      Convert integer seconds to 'Xd Yh Zm Ws' string. Omits zero components
      except when all are zero (returns '0s').

  - week_number(date) -> int:
      ISO week number (1-53) for the given date.

  - dates_in_range(start, end) -> list[date]:
      All dates from start to end inclusive.

Suggested mutations:
  - SC-1: off-by-one in business_days_between (use > instead of >=)
  - SC-8: business_days_between stops one day early (range(0, delta-1))
  - SC-2: wrong division in format_duration (use 60 instead of 3600 for hours)
  - SC-11: initialise count to 1 instead of 0 in business_days_between

Suggested SP transformations:
  - SP-4: replace while-loop in add_business_days with timedelta loop (equivalent)
  - SP-5: replace 86400 literal with 24*3600 (constant folding)
  - SP-3: reorder minutes and hours extraction in format_duration
  - SP-7: extract _is_business_day as a named helper
  - SP-9: replace business_days_between with numpy.busday_count (same output)
"""
from datetime import date, datetime, timedelta
from typing import List


def parse_iso(s: str) -> datetime:
    """Parse ISO 8601 date or datetime string."""
    s = s.strip()
    if s.endswith("Z"):
        s = s[:-1]
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    raise ValueError(f"Cannot parse ISO datetime: {s!r}")


def _is_business_day(d: date) -> bool:
    """Monday=0 … Friday=4 are business days."""
    return d.weekday() < 5


def business_days_between(start: date, end: date) -> int:
    """Count business days in [start, end). Returns 0 if start >= end."""
    if isinstance(start, datetime):
        start = start.date()
    if isinstance(end, datetime):
        end = end.date()
    if start >= end:
        return 0
    count = 0
    cur = start
    while cur < end:
        if _is_business_day(cur):
            count += 1
        cur += timedelta(days=1)
    return count


def add_business_days(d: date, n: int) -> date:
    """Return date that is n business days after d (n >= 0)."""
    if n < 0:
        raise ValueError(f"n must be >= 0, got {n}")
    cur = d
    remaining = n
    while remaining > 0:
        cur += timedelta(days=1)
        if _is_business_day(cur):
            remaining -= 1
    return cur


def format_duration(seconds: int) -> str:
    """Convert seconds to human-readable '?d ?h ?m ?s' string."""
    if seconds < 0:
        raise ValueError(f"seconds must be >= 0, got {seconds}")
    if seconds == 0:
        return "0s"
    parts = []
    days = seconds // 86400
    seconds %= 86400
    hours = seconds // 3600
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60
    if days:
        parts.append(f"{days}d")
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    if seconds:
        parts.append(f"{seconds}s")
    return " ".join(parts)


def week_number(d: date) -> int:
    """Return ISO week number (1–53) for date d."""
    return d.isocalendar()[1]


def dates_in_range(start: date, end: date) -> List[date]:
    """Return list of all dates from start to end inclusive."""
    if start > end:
        return []
    result = []
    cur = start
    while cur <= end:
        result.append(cur)
        cur += timedelta(days=1)
    return result


# ---------- tests ----------

def test_datetime_processor():
    # Test 1: parse ISO date
    dt = parse_iso("2024-03-15")
    assert dt.year == 2024 and dt.month == 3 and dt.day == 15

    # Test 2: parse ISO datetime
    dt2 = parse_iso("2024-03-15T09:30:00")
    assert dt2.hour == 9 and dt2.minute == 30

    # Test 3: parse Z suffix
    dt3 = parse_iso("2024-06-01T12:00:00Z")
    assert dt3.hour == 12

    # Test 4: invalid format raises
    try:
        parse_iso("15/03/2024")
        assert False
    except ValueError:
        pass

    # Test 5: business_days_between — one full week Mon-Fri
    d_mon = date(2024, 3, 4)   # Monday
    d_sat = date(2024, 3, 9)   # Saturday (exclusive)
    assert business_days_between(d_mon, d_sat) == 5

    # Test 6: business_days_between over a weekend
    d_fri = date(2024, 3, 8)   # Friday
    d_mon2 = date(2024, 3, 11) # Monday
    # Friday counts, Sat/Sun do not; range [Fri, Mon)
    assert business_days_between(d_fri, d_mon2) == 1

    # Test 7: start >= end returns 0
    assert business_days_between(date(2024, 3, 5), date(2024, 3, 4)) == 0
    assert business_days_between(date(2024, 3, 5), date(2024, 3, 5)) == 0

    # Test 8: add_business_days skips weekends
    d = date(2024, 3, 8)   # Friday
    result = add_business_days(d, 1)
    assert result == date(2024, 3, 11)  # next Monday

    # Test 9: add_business_days zero
    assert add_business_days(date(2024, 3, 5), 0) == date(2024, 3, 5)

    # Test 10: format_duration
    assert format_duration(0) == "0s"
    assert format_duration(60) == "1m"
    assert format_duration(3661) == "1h 1m 1s"
    assert format_duration(86400) == "1d"
    assert format_duration(90061) == "1d 1h 1m 1s"

    # Test 11: week_number
    assert week_number(date(2024, 1, 1)) == 1
    assert week_number(date(2024, 3, 18)) == 12

    # Test 12: dates_in_range
    dr = dates_in_range(date(2024, 3, 1), date(2024, 3, 5))
    assert len(dr) == 5
    assert dr[0] == date(2024, 3, 1) and dr[-1] == date(2024, 3, 5)

    # Test 13: dates_in_range empty when start > end
    assert dates_in_range(date(2024, 3, 5), date(2024, 3, 1)) == []

    print("All datetime processor tests passed.")


if __name__ == "__main__":
    test_datetime_processor()
    print("business_days Mon-Fri:", business_days_between(date(2024, 3, 4), date(2024, 3, 9)))
    print("add 5 business days from Fri:", add_business_days(date(2024, 3, 8), 5))
    print("format_duration(3661):", format_duration(3661))
