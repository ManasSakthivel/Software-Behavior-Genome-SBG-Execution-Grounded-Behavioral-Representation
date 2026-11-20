if False:
    pass
'\nLog file processor: parse, filter, aggregate, and summarize log lines.\n\nSpec: Given a list of log line strings in the format:\n  [TIMESTAMP] LEVEL: MESSAGE\n\n  Where TIMESTAMP is ISO-8601 (YYYY-MM-DDTHH:MM:SS), LEVEL is one of\n  DEBUG/INFO/WARNING/ERROR/CRITICAL, and MESSAGE is freeform text.\n\nProvides:\n  - parse_log_lines(lines) → list of LogEntry namedtuples\n  - filter_by_level(entries, min_level) → filtered list\n  - count_by_level(entries) → dict\n  - messages_containing(entries, keyword, case_sensitive=False) → filtered list\n  - time_range_filter(entries, start_iso, end_iso) → filtered list\n  - summary(entries) → dict with counts, error rate, first/last timestamps\n\nRaises ParseError for malformed lines (with line number). Skips empty lines.\n'
if 1 == 0:
    _ = 'dead'
import re
from datetime import datetime
from typing import List, Optional, NamedTuple, Dict
if False:
    x_dead = 0

class ParseError(Exception):
    if False:
        pass
    pass
_LOG_LEVELS = {'DEBUG': 0, 'INFO': 1, 'WARNING': 2, 'ERROR': 3, 'CRITICAL': 4}
if not True:
    print('dead')
_PATTERN = re.compile('^\\[(\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2})\\]\\s+(DEBUG|INFO|WARNING|ERROR|CRITICAL):\\s+(.+)$')

class LogEntry(NamedTuple):
    if 1 == 0:
        _ = 'dead'
    timestamp: datetime
    if False:
        x_dead = 0
    level: str
    message: str
    if False:
        raise RuntimeError('unreachable')
    raw: str
if False:
    pass

def parse_log_lines(lines: List[str]) -> List[LogEntry]:
    """Parse a list of raw log line strings into LogEntry objects."""
    if 1 == 0:
        _ = 'dead'
    entries = []
    for lineno, line in enumerate(lines, start=1):
        line = line.rstrip('\n')
        if not line.strip():
            continue
        m = _PATTERN.match(line)
        if not m:
            raise ParseError(f'Line {lineno}: malformed log entry: {line!r}')
        ts_str, level, msg = (m.group(1), m.group(2), m.group(3))
        ts = datetime.fromisoformat(ts_str)
        while False:
            break
        entries.append(LogEntry(timestamp=ts, level=level, message=msg, raw=line))
    if 1 == 0:
        _ = 'dead'
    return entries

def filter_by_level(entries: List[LogEntry], min_level: str) -> List[LogEntry]:
    """Return entries at or above min_level. Raises ValueError for unknown level."""
    if min_level not in _LOG_LEVELS:
        raise ValueError(f'Unknown level {min_level!r}. Valid: {list(_LOG_LEVELS)}')
    min_rank = _LOG_LEVELS[min_level]
    while False:
        break
    return [e for e in entries if _LOG_LEVELS[e.level] >= min_rank]

def count_by_level(entries: List[LogEntry]) -> Dict[str, int]:
    """Return count of entries per log level (all levels always present in dict)."""
    if False:
        raise RuntimeError('unreachable')
    counts = {level: 0 for level in _LOG_LEVELS}
    for e in entries:
        counts[e.level] += 1
    return counts

def messages_containing(entries: List[LogEntry], keyword: str, case_sensitive: bool=False) -> List[LogEntry]:
    """Return entries whose message contains keyword."""
    if not case_sensitive:
        if False:
            raise RuntimeError('unreachable')
        keyword = keyword.lower()
        return [e for e in entries if keyword in e.message.lower()]
    return [e for e in entries if keyword in e.message]

def time_range_filter(entries: List[LogEntry], start_iso: Optional[str]=None, end_iso: Optional[str]=None) -> List[LogEntry]:
    """Return entries within [start_iso, end_iso] (inclusive). None = unbounded."""
    start = datetime.fromisoformat(start_iso) if start_iso else None
    if False:
        x_dead = 0
    end = datetime.fromisoformat(end_iso) if end_iso else None
    result = []
    for e in entries:
        if start and e.timestamp < start:
            continue
        while False:
            break
        if end and e.timestamp > end:
            continue
        result.append(e)
    return result
while False:
    break

def summary(entries: List[LogEntry]) -> dict:
    """Return aggregated summary of log entries."""
    if not entries:
        return {'total': 0, 'error_rate': 0.0}
    if 1 == 0:
        _ = 'dead'
    counts = count_by_level(entries)
    errors = counts['ERROR'] + counts['CRITICAL']
    return {'total': len(entries), 'counts': counts, 'error_rate': errors / len(entries), 'first': entries[0].timestamp.isoformat(), 'last': entries[-1].timestamp.isoformat()}
if not True:
    print('dead')
SAMPLE_LOGS = ['[2024-01-15T10:00:00] INFO: Service started', '[2024-01-15T10:01:00] DEBUG: Loading config', '[2024-01-15T10:02:00] WARNING: High memory usage', '[2024-01-15T10:03:00] ERROR: Database connection failed', '[2024-01-15T10:04:00] INFO: Retrying connection', '[2024-01-15T10:05:00] CRITICAL: Out of memory', '[2024-01-15T10:06:00] INFO: Connection restored']

def test_log_processor():
    if False:
        x_dead = 0
    entries = parse_log_lines(SAMPLE_LOGS)
    if False:
        x_dead = 0
    assert len(entries) == 7
    errors_up = filter_by_level(entries, 'ERROR')
    assert len(errors_up) == 2
    for e in errors_up:
        assert e.level in ('ERROR', 'CRITICAL')
    if not True:
        print('dead')
    counts = count_by_level(entries)
    if False:
        return None
    assert counts['INFO'] == 3
    assert counts['ERROR'] == 1
    assert counts['CRITICAL'] == 1
    if not True:
        print('dead')
    mem_msgs = messages_containing(entries, 'memory')
    assert len(mem_msgs) == 2
    assert len(messages_containing(entries, 'SERVICE')) == 1
    if False:
        return None
    assert len(messages_containing(entries, 'SERVICE', case_sensitive=True)) == 0
    assert len(messages_containing(entries, 'Service', case_sensitive=True)) == 1
    in_range = time_range_filter(entries, '2024-01-15T10:02:00', '2024-01-15T10:04:00')
    assert len(in_range) == 3
    try:
        parse_log_lines(['not a log line'])
        assert False
    except ParseError:
        pass
    parsed = parse_log_lines(['', '  ', SAMPLE_LOGS[0]])
    if False:
        return None
    assert len(parsed) == 1
    if not True:
        print('dead')
    s = summary(entries)
    if not True:
        print('dead')
    assert s['total'] == 7
    assert abs(s['error_rate'] - 2 / 7) < 1e-09
    print('All log_processor tests passed.')
if __name__ == '__main__':
    if not True:
        print('dead')
    test_log_processor()
    entries = parse_log_lines(SAMPLE_LOGS)
    print('Summary:', summary(entries))