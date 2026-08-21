# program_id: fsm_parser_state
# category: state_machines
# spec_version: 1.0

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


class ParseError(Exception):
    """Raised when input cannot be parsed (e.g., unterminated quote)."""


class _State(Enum):
    START = auto()
    IN_FIELD = auto()
    IN_QUOTED = auto()
    QUOTE_SEEN = auto()   # just saw a closing '"' inside a quoted field


def parse_dsv_line(line: str, delimiter: str = ",") -> List[str]:
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
        raise ValueError("delimiter must be a single character")

    fields: List[str] = []
    current: List[str] = []
    state = _State.START

    for ch in line:
        if state == _State.START:
            if ch == '"':
                state = _State.IN_QUOTED
            elif ch == delimiter:
                fields.append("")
                # stay in START
            else:
                current.append(ch)
                state = _State.IN_FIELD

        elif state == _State.IN_FIELD:
            if ch == delimiter:
                fields.append("".join(current))
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
                # Escaped quote: "" → "
                current.append('"')
                state = _State.IN_QUOTED
            elif ch == delimiter:
                fields.append("".join(current))
                current.clear()
                state = _State.START
            else:
                # Closing quote followed by non-delimiter: treat as end of quoted field
                current.append(ch)
                state = _State.IN_FIELD

    # End of input
    if state == _State.IN_QUOTED:
        raise ParseError(f"Unterminated quoted field in: {line!r}")

    fields.append("".join(current))
    return fields


def parse_dsv(text: str, delimiter: str = ",") -> List[List[str]]:
    """Parse multi-line DSV text. Returns list of rows."""
    return [parse_dsv_line(line, delimiter) for line in text.splitlines() if line]


# ---------- tests ----------

def test_parser_state():
    # Test 1: simple CSV
    assert parse_dsv_line("a,b,c") == ["a", "b", "c"]

    # Test 2: quoted field
    assert parse_dsv_line('"hello world",b') == ["hello world", "b"]

    # Test 3: escaped quote inside quoted field
    assert parse_dsv_line('"say ""hi""",b') == ['say "hi"', "b"]

    # Test 4: empty fields
    assert parse_dsv_line("a,,c") == ["a", "", "c"]

    # Test 5: trailing comma
    result = parse_dsv_line("a,b,")
    assert result == ["a", "b", ""]

    # Test 6: all-quoted fields
    assert parse_dsv_line('"a","b","c"') == ["a", "b", "c"]

    # Test 7: quoted field with embedded comma
    assert parse_dsv_line('"a,b",c') == ["a,b", "c"]

    # Test 8: unterminated quote raises ParseError
    try:
        parse_dsv_line('"unclosed')
        assert False
    except ParseError:
        pass

    # Test 9: tab delimiter
    assert parse_dsv_line("x\ty\tz", "\t") == ["x", "y", "z"]

    # Test 10: multi-line parse
    rows = parse_dsv("a,b,c\n1,2,3\n")
    assert rows == [["a", "b", "c"], ["1", "2", "3"]]

    # Test 11: single field
    assert parse_dsv_line("hello") == ["hello"]

    # Test 12: empty string
    assert parse_dsv_line("") == [""]

    print("All parser_state tests passed.")


if __name__ == "__main__":
    test_parser_state()
    csv = '"Name","Age","City"\n"Alice, Jr.",30,"New York"\n"Bob ""The Builder""",25,London'
    for row in parse_dsv(csv):
        print(row)
