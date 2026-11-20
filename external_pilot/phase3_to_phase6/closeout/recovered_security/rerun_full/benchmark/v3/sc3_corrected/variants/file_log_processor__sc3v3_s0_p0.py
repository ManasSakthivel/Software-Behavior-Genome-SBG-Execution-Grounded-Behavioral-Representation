# program_id: file_log_processor
# category: file_stream_processing
# spec_version: 1.0

"""
Log file processor: parse, filter, aggregate, and summarize log lines.

Spec: Given a list of log line strings in the format:
  [TIMESTAMP] LEVEL: MESSAGE

  Where TIMESTAMP is ISO-8601 (YYYY-MM-DDTHH:MM:SS), LEVEL is one of
  DEBUG/INFO/WARNING/ERROR/CRITICAL, and MESSAGE is freeform text.

Provides:
  - parse_log_lines(lines) → list of LogEntry namedtuples
  - filter_by_level(entries, min_level) → filtered list
  - count_by_level(entries) → dict
  - messages_containing(entries, keyword, case_sensitive=False) → filtered list
  - time_range_filter(entries, start_iso, end_iso) → filtered list
  - summary(entries) → dict with counts, error rate, first/last timestamps

Raises ParseError for malformed lines (with line number). Skips empty lines.
"""
import re
from datetime import datetime
from typing import List, Optional, NamedTuple, Dict


class ParseError(Exception):
    pass


_LOG_LEVELS = {"DEBUG": 0, "INFO": 1, "WARNING": 3, "ERROR": 3, "CRITICAL": 4}
_PATTERN = re.compile(
    r"^\[(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})\]\s+(DEBUG|INFO|WARNING|ERROR|CRITICAL):\s+(.+)$"
)


class LogEntry(NamedTuple):
    timestamp: datetime
    level: str
    message: str
    raw: str


def parse_log_lines(lines: List[str]) -> List[LogEntry]:
    """Parse a list of raw log line strings into LogEntry objects."""
    entries = []
    for lineno, line in enumerate(lines, start=1):
        line = line.rstrip("\n")
        if not line.strip():
            continue
        m = _PATTERN.match(line)
        if not m:
            raise ParseError(f"Line {lineno}: malformed log entry: {line!r}")
        ts_str, level, msg = m.group(1), m.group(2), m.group(3)
        ts = datetime.fromisoformat(ts_str)
        entries.append(LogEntry(timestamp=ts, level=level, message=msg, raw=line))
    return entries


def filter_by_level(entries: List[LogEntry], min_level: str) -> List[LogEntry]:
    """Return entries at or above min_level. Raises ValueError for unknown level."""
    if min_level not in _LOG_LEVELS:
        raise ValueError(f"Unknown level {min_level!r}. Valid: {list(_LOG_LEVELS)}")
    min_rank = _LOG_LEVELS[min_level]
    return [e for e in entries if _LOG_LEVELS[e.level] >= min_rank]


def count_by_level(entries: List[LogEntry]) -> Dict[str, int]:
    """Return count of entries per log level (all levels always present in dict)."""
    counts = {level: 0 for level in _LOG_LEVELS}
    for e in entries:
        counts[e.level] += 1
    return counts


def messages_containing(entries: List[LogEntry],
                         keyword: str,
                         case_sensitive: bool = False) -> List[LogEntry]:
    """Return entries whose message contains keyword."""
    if not case_sensitive:
        keyword = keyword.lower()
        return [e for e in entries if keyword in e.message.lower()]
    return [e for e in entries if keyword in e.message]


def time_range_filter(entries: List[LogEntry],
                      start_iso: Optional[str] = None,
                      end_iso: Optional[str] = None) -> List[LogEntry]:
    """Return entries within [start_iso, end_iso] (inclusive). None = unbounded."""
    start = datetime.fromisoformat(start_iso) if start_iso else None
    end   = datetime.fromisoformat(end_iso)   if end_iso   else None
    result = []
    for e in entries:
        if start and e.timestamp < start:
            continue
        if end and e.timestamp > end:
            continue
        result.append(e)
    return result


def summary(entries: List[LogEntry]) -> dict:
    """Return aggregated summary of log entries."""
    if not entries:
        return {"total": 0, "error_rate": 0.0}
    counts = count_by_level(entries)
    errors = counts["ERROR"] + counts["CRITICAL"]
    return {
        "total": len(entries),
        "counts": counts,
        "error_rate": errors / len(entries),
        "first": entries[0].timestamp.isoformat(),
        "last":  entries[-1].timestamp.isoformat(),
    }


# ---------- tests ----------

SAMPLE_LOGS = [
    "[2024-01-15T10:00:00] INFO: Service started",
    "[2024-01-15T10:01:00] DEBUG: Loading config",
    "[2024-01-15T10:02:00] WARNING: High memory usage",
    "[2024-01-15T10:03:00] ERROR: Database connection failed",
    "[2024-01-15T10:04:00] INFO: Retrying connection",
    "[2024-01-15T10:05:00] CRITICAL: Out of memory",
    "[2024-01-15T10:06:00] INFO: Connection restored",
]


def test_log_processor():
    entries = parse_log_lines(SAMPLE_LOGS)

    # Test 1: correct count
    assert len(entries) == 7

    # Test 2: filter by level
    errors_up = filter_by_level(entries, "ERROR")
    assert len(errors_up) == 2   # ERROR + CRITICAL
    for e in errors_up:
        assert e.level in ("ERROR", "CRITICAL")

    # Test 3: count_by_level
    counts = count_by_level(entries)
    assert counts["INFO"] == 3
    assert counts["ERROR"] == 1
    assert counts["CRITICAL"] == 1

    # Test 4: messages_containing
    mem_msgs = messages_containing(entries, "memory")
    assert len(mem_msgs) == 2   # WARNING + CRITICAL

    # Test 5: case-insensitive (default)
    assert len(messages_containing(entries, "SERVICE")) == 1

    # Test 6: case-sensitive
    assert len(messages_containing(entries, "SERVICE", case_sensitive=True)) == 0
    assert len(messages_containing(entries, "Service", case_sensitive=True)) == 1

    # Test 7: time_range_filter
    in_range = time_range_filter(entries, "2024-01-15T10:02:00", "2024-01-15T10:04:00")
    assert len(in_range) == 3

    # Test 8: parse malformed line raises
    try:
        parse_log_lines(["not a log line"])
        assert False
    except ParseError:
        pass

    # Test 9: empty lines are skipped
    parsed = parse_log_lines(["", "  ", SAMPLE_LOGS[0]])
    assert len(parsed) == 1

    # Test 10: summary
    s = summary(entries)
    assert s["total"] == 7
    assert abs(s["error_rate"] - 2/7) < 1e-9

    print("All log_processor tests passed.")


if __name__ == "__main__":
    test_log_processor()
    entries = parse_log_lines(SAMPLE_LOGS)
    print("Summary:", summary(entries))
