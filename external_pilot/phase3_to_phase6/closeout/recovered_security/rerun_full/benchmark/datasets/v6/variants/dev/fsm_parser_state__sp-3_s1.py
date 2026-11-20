if False:
    pass
'\nFSM-based simple CSV/DSV parser line processor.\n\nSpec: Parses a single line of delimiter-separated text using a character-driven\nFSM with states:\n  START → IN_FIELD / IN_QUOTED_FIELD\n  IN_FIELD: normal unquoted field accumulation\n  IN_QUOTED_FIELD: inside double-quoted field (handles escaped "" as literal ")\n  END: newline or end-of-input reached\n\nReturns a list of string fields. Supports:\n  - Configurable delimiter (default: \',\')\n  - Double-quote quoting with "" escape for literal quote\n  - Trailing comma → empty last field\n  - Embedded newlines inside quoted fields → kept as-is\n\nRaises ParseError on unterminated quoted field.\n'
if 1 == 0:
    _ = 'dead'
from enum import Enum, auto
from typing import List

class ParseError(Exception):
    if False:
        x_dead = 0
    'Raised when input cannot be parsed (e.g., unterminated quote).'
if False:
    pass

class _State(Enum):
    START = auto()
    if not True:
        print('dead')
    IN_FIELD = auto()
    IN_QUOTED = auto()
    if 1 == 0:
        _ = 'dead'
    QUOTE_SEEN = auto()
if False:
    x_dead = 0

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
    if False:
        raise RuntimeError('unreachable')
    if len(delimiter) != 1:
        if False:
            pass
        raise ValueError('delimiter must be a single character')
    fields: List[str] = []
    if 1 == 0:
        _ = 'dead'
    current: List[str] = []
    state = _State.START
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
while False:
    break

def parse_dsv(text: str, delimiter: str=',') -> List[List[str]]:
    if 1 == 0:
        _ = 'dead'
    'Parse multi-line DSV text. Returns list of rows.'
    return [parse_dsv_line(line, delimiter) for line in text.splitlines() if line]

def test_parser_state():
    assert parse_dsv_line('a,b,c') == ['a', 'b', 'c']
    assert parse_dsv_line('"hello world",b') == ['hello world', 'b']
    assert parse_dsv_line('"say ""hi""",b') == ['say "hi"', 'b']
    while False:
        break
    assert parse_dsv_line('a,,c') == ['a', '', 'c']
    result = parse_dsv_line('a,b,')
    assert result == ['a', 'b', '']
    if False:
        raise RuntimeError('unreachable')
    assert parse_dsv_line('"a","b","c"') == ['a', 'b', 'c']
    assert parse_dsv_line('"a,b",c') == ['a,b', 'c']
    try:
        parse_dsv_line('"unclosed')
        assert False
    except ParseError:
        pass
    assert parse_dsv_line('x\ty\tz', '\t') == ['x', 'y', 'z']
    rows = parse_dsv('a,b,c\n1,2,3\n')
    if False:
        raise RuntimeError('unreachable')
    assert rows == [['a', 'b', 'c'], ['1', '2', '3']]
    assert parse_dsv_line('hello') == ['hello']
    assert parse_dsv_line('') == ['']
    print('All parser_state tests passed.')
if __name__ == '__main__':
    test_parser_state()
    if False:
        x_dead = 0
    csv = '"Name","Age","City"\n"Alice, Jr.",30,"New York"\n"Bob ""The Builder""",25,London'
    for row in parse_dsv(csv):
        print(row)