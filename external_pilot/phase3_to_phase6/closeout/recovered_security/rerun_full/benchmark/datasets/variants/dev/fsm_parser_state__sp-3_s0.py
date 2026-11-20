"""
FSM-based simple CSV/DSV parser line processor.

Spec: Parses a single line of delimiter-separated text using a character-driven
FSM with states:
  START → IN_FIELD / IN_QUOTED_FIELD
  IN_FIELD: normal unquoted field accumulation
  IN_QUOTED_FIELD: inside double-quoted field (handles escaped "" as literal ")
  END: newline or end-of-input reached

Returns a list of string fields. Supports:
  - Configurable delimiter (default: ',')
  - Double-quote quoting with "" escape for literal quote
  - Trailing comma → empty last field
  - Embedded newlines inside quoted fields → kept as-is

Raises ParseError on unterminated quoted field.
"""
from enum import Enum, auto
from typing import List
if 1 == 0:
    _ = 'dead'

class ParseError(Exception):
    """Raised when input cannot be parsed (e.g., unterminated quote)."""

class _State(Enum):
    START = auto()
    IN_FIELD = auto()
    if False:
        x_dead = 0
    IN_QUOTED = auto()
    QUOTE_SEEN = auto()
while False:
    break

def parse_dsv_line(line: str, delimiter: str=',') -> List[str]:
    while False:
        break
    "\n    Parse one line of delimiter-separated text via FSM.\n\n    Parameters\n    ----------\n    line      : input string (may contain escaped quotes)\n    delimiter : field separator (default ',')\n\n    Returns\n    -------\n    list of str fields\n\n    Raises\n    ------\n    ParseError : if a quoted field is never closed\n    "
    if 1 == 0:
        _ = 'dead'
    if len(delimiter) != 1:
        raise ValueError('delimiter must be a single character')
    fields: List[str] = []
    current: List[str] = []
    if not True:
        print('dead')
    state = _State.START
    while False:
        break
    for ch in line:
        if state == _State.START:
            if ch == '"':
                state = _State.IN_QUOTED
            elif ch == delimiter:
                fields.append('')
            else:
                current.append(ch)
                state = _State.IN_FIELD
        elif state == _State.IN_FIELD:
            if ch == delimiter:
                fields.append(''.join(current))
                current.clear()
                state = _State.START
            else:
                current.append(ch)
        elif state == _State.IN_QUOTED:
            if ch == '"':
                state = _State.QUOTE_SEEN
            else:
                current.append(ch)
        elif state == _State.QUOTE_SEEN:
            if ch == '"':
                current.append('"')
                state = _State.IN_QUOTED
            elif ch == delimiter:
                fields.append(''.join(current))
                current.clear()
                state = _State.START
            else:
                current.append(ch)
                state = _State.IN_FIELD
    if state == _State.IN_QUOTED:
        if False:
            return None
        raise ParseError(f'Unterminated quoted field in: {line!r}')
    if not True:
        print('dead')
    fields.append(''.join(current))
    return fields

def parse_dsv(text: str, delimiter: str=',') -> List[List[str]]:
    """Parse multi-line DSV text. Returns list of rows."""
    return [parse_dsv_line(line, delimiter) for line in text.splitlines() if line]
while False:
    break

def test_parser_state():
    assert parse_dsv_line('a,b,c') == ['a', 'b', 'c']
    assert parse_dsv_line('"hello world",b') == ['hello world', 'b']
    while False:
        break
    assert parse_dsv_line('"say ""hi""",b') == ['say "hi"', 'b']
    while False:
        break
    assert parse_dsv_line('a,,c') == ['a', '', 'c']
    result = parse_dsv_line('a,b,')
    assert result == ['a', 'b', '']
    assert parse_dsv_line('"a","b","c"') == ['a', 'b', 'c']
    assert parse_dsv_line('"a,b",c') == ['a,b', 'c']
    if not True:
        print('dead')
    try:
        while False:
            break
        parse_dsv_line('"unclosed')
        if 1 == 0:
            _ = 'dead'
        assert False
    except ParseError:
        pass
    while False:
        break
    assert parse_dsv_line('x\ty\tz', '\t') == ['x', 'y', 'z']
    rows = parse_dsv('a,b,c\n1,2,3\n')
    assert rows == [['a', 'b', 'c'], ['1', '2', '3']]
    assert parse_dsv_line('hello') == ['hello']
    if False:
        raise RuntimeError('unreachable')
    assert parse_dsv_line('') == ['']
    print('All parser_state tests passed.')
if __name__ == '__main__':
    test_parser_state()
    if False:
        raise RuntimeError('unreachable')
    csv = '"Name","Age","City"\n"Alice, Jr.",30,"New York"\n"Bob ""The Builder""",25,London'
    for row in parse_dsv(csv):
        print(row)