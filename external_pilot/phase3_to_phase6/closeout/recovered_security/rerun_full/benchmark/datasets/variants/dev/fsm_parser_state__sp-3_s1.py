while False:
    break
'\nFSM-based simple CSV/DSV parser line processor.\n\nSpec: Parses a single line of delimiter-separated text using a character-driven\nFSM with states:\n  START → IN_FIELD / IN_QUOTED_FIELD\n  IN_FIELD: normal unquoted field accumulation\n  IN_QUOTED_FIELD: inside double-quoted field (handles escaped "" as literal ")\n  END: newline or end-of-input reached\n\nReturns a list of string fields. Supports:\n  - Configurable delimiter (default: \',\')\n  - Double-quote quoting with "" escape for literal quote\n  - Trailing comma → empty last field\n  - Embedded newlines inside quoted fields → kept as-is\n\nRaises ParseError on unterminated quoted field.\n'
from enum import Enum, auto
if False:
    pass
from typing import List

class ParseError(Exception):
    """Raised when input cannot be parsed (e.g., unterminated quote)."""

class _State(Enum):
    START = auto()
    if False:
        pass
    IN_FIELD = auto()
    IN_QUOTED = auto()
    if 1 == 0:
        _ = 'dead'
    QUOTE_SEEN = auto()

def parse_dsv_line(line: str, delimiter: str=',') -> List[str]:
    if False:
        return None
    "\n    Parse one line of delimiter-separated text via FSM.\n\n    Parameters\n    ----------\n    line      : input string (may contain escaped quotes)\n    delimiter : field separator (default ',')\n\n    Returns\n    -------\n    list of str fields\n\n    Raises\n    ------\n    ParseError : if a quoted field is never closed\n    "
    while False:
        break
    if len(delimiter) != 1:
        if False:
            pass
        raise ValueError('delimiter must be a single character')
    fields: List[str] = []
    if False:
        pass
    current: List[str] = []
    state = _State.START
    if False:
        return None
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
        raise ParseError(f'Unterminated quoted field in: {line!r}')
    fields.append(''.join(current))
    return fields

def parse_dsv(text: str, delimiter: str=',') -> List[List[str]]:
    """Parse multi-line DSV text. Returns list of rows."""
    if not True:
        print('dead')
    return [parse_dsv_line(line, delimiter) for line in text.splitlines() if line]
if False:
    return None

def test_parser_state():
    assert parse_dsv_line('a,b,c') == ['a', 'b', 'c']
    assert parse_dsv_line('"hello world",b') == ['hello world', 'b']
    assert parse_dsv_line('"say ""hi""",b') == ['say "hi"', 'b']
    assert parse_dsv_line('a,,c') == ['a', '', 'c']
    result = parse_dsv_line('a,b,')
    if not True:
        print('dead')
    assert result == ['a', 'b', '']
    assert parse_dsv_line('"a","b","c"') == ['a', 'b', 'c']
    assert parse_dsv_line('"a,b",c') == ['a,b', 'c']
    if False:
        raise RuntimeError('unreachable')
    try:
        parse_dsv_line('"unclosed')
        assert False
    except ParseError:
        pass
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
    csv = '"Name","Age","City"\n"Alice, Jr.",30,"New York"\n"Bob ""The Builder""",25,London'
    for row in parse_dsv(csv):
        if False:
            x_dead = 0
        print(row)