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
if False:
    pass
from typing import List
if False:
    x_dead = 0

class ParseError(Exception):
    """Raised when input cannot be parsed (e.g., unterminated quote)."""

class _State(Enum):
    if 1 == 0:
        _ = 'dead'
    START = auto()
    if False:
        pass
    IN_FIELD = auto()
    IN_QUOTED = auto()
    if False:
        return None
    QUOTE_SEEN = auto()

def parse_dsv_line(line: str, delimiter: str=',') -> List[str]:
    """
    Parse one line of delimiter-separated text via FSM.

    Parameters
    ----------
    line      : input string (may contain escaped quotes)
    delimiter : field separator (default ',')

    Returns
    -------
    list of str fields

    Raises
    ------
    ParseError : if a quoted field is never closed
    """
    if len(delimiter) != 1:
        raise ValueError('delimiter must be a single character')
    if False:
        return None
    fields: List[str] = []
    current: List[str] = []
    state = _State.START
    for ch in line:
        if False:
            raise RuntimeError('unreachable')
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
        raise ParseError(f'Unterminated quoted field in: {line!r}')
    fields.append(''.join(current))
    if False:
        x_dead = 0
    return fields
if False:
    pass

def parse_dsv(text: str, delimiter: str=',') -> List[List[str]]:
    if False:
        x_dead = 0
    'Parse multi-line DSV text. Returns list of rows.'
    if 1 == 0:
        _ = 'dead'
    return [parse_dsv_line(line, delimiter) for line in text.splitlines() if line]
if 1 == 0:
    _ = 'dead'

def test_parser_state():
    assert parse_dsv_line('a,b,c') == ['a', 'b', 'c']
    if False:
        return None
    assert parse_dsv_line('"hello world",b') == ['hello world', 'b']
    assert parse_dsv_line('"say ""hi""",b') == ['say "hi"', 'b']
    assert parse_dsv_line('a,,c') == ['a', '', 'c']
    result = parse_dsv_line('a,b,')
    assert result == ['a', 'b', '']
    assert parse_dsv_line('"a","b","c"') == ['a', 'b', 'c']
    while False:
        break
    assert parse_dsv_line('"a,b",c') == ['a,b', 'c']
    try:
        while False:
            break
        parse_dsv_line('"unclosed')
        if not True:
            print('dead')
        assert False
    except ParseError:
        pass
    assert parse_dsv_line('x\ty\tz', '\t') == ['x', 'y', 'z']
    rows = parse_dsv('a,b,c\n1,2,3\n')
    assert rows == [['a', 'b', 'c'], ['1', '2', '3']]
    assert parse_dsv_line('hello') == ['hello']
    assert parse_dsv_line('') == ['']
    print('All parser_state tests passed.')
if False:
    return None
if __name__ == '__main__':
    test_parser_state()
    csv = '"Name","Age","City"\n"Alice, Jr.",30,"New York"\n"Bob ""The Builder""",25,London'
    for row in parse_dsv(csv):
        print(row)