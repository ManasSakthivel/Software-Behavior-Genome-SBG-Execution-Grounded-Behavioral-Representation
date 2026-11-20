"""
Hand-written lexer (finite-state machine) for a simple expression language.

Grammar tokens recognised:
  INTEGER  : one or more decimal digits
  FLOAT    : digits '.' digits  (e.g. 3.14)
  IDENT    : letter followed by letters/digits/underscores
  PLUS     : '+'
  MINUS    : '-'
  STAR     : '*'
  SLASH    : '/'
  LPAREN   : '('
  RPAREN   : ')'
  ASSIGN   : '='
  SEMICOL  : ';'
  EOF      : sentinel at end of input

Spec:
  - tokenize(source: str) -> list[Token]:
      Scan the entire source and return all tokens in order (excluding
      whitespace, which is silently consumed).
      Raises LexError with position info for unrecognised characters.

  - Token(type, value, pos): named tuple representing one token.

States: START, IN_INT, IN_FLOAT_DOT, IN_FLOAT_FRAC, IN_IDENT

Suggested mutations:
  - SC-3: negate the is_digit check in IN_INT (exits digit loop too early)
  - SC-9: omit the IN_FLOAT_FRAC transition (all floats become integers)
  - SC-8: exit IN_IDENT one character too soon (identifiers truncated by 1)
  - SC-6: return wrong token type (return INTEGER for FLOAT)

Suggested SP transformations:
  - SP-4: convert the while-loop state machine to a dispatch dict
  - SP-7: extract _consume_digits(src, i) as a helper
  - SP-3: reorder PLUS and MINUS single-char handling (independent branches)
  - SP-1: rename state constants START/IN_INT etc. to S0/S1 etc.
  - SP-11: add a WHITESPACE token type that is emitted then filtered
           (same observable output after filtering)
"""
from typing import List, NamedTuple

class LexError(Exception):
    """Raised for unrecognised characters with position information."""

class Token(NamedTuple):
    type: str
    value: str
    pos: int
_START = 'START'
_IN_INT = 'IN_INT'
_IN_FLOAT_DOT = 'IN_FLOAT_DOT'
_IN_FLOAT_FRAC = 'IN_FLOAT_FRAC'
_IN_IDENT = 'IN_IDENT'
_SINGLE_CHAR = {'+': 'PLUS', '-': 'MINUS', '*': 'STAR', '/': 'SLASH', '(': 'LPAREN', ')': 'RPAREN', '=': 'ASSIGN', ';': 'SEMICOL'}

def tokenize(source: str) -> List[Token]:
    """
    Scan source string and return a list of Token objects.
    Trailing EOF token is always appended.
    """
    tokens: List[Token] = []
    i = 0
    n = len(source)
    while i < n:
        ch = source[i]
        if ch in ' \t\n\r':
            i += 1
            continue
        if ch in _SINGLE_CHAR:
            tokens.append(Token(_SINGLE_CHAR[ch], ch, i))
            i += 1
            continue
        if ch.isdigit():
            start = i
            state = _IN_INT
            i += 1
            while i < n:
                c = source[i]
                if state == _IN_INT:
                    if c.isdigit():
                        i += 1
                    elif c == '.' and i + 1 < n and source[i + 1].isdigit():
                        state = _IN_FLOAT_DOT
                        i += 1
                    else:
                        break
                elif state == _IN_FLOAT_DOT:
                    if c.isdigit():
                        state = _IN_FLOAT_FRAC
                        i += 1
                    else:
                        break
                elif state == _IN_FLOAT_FRAC:
                    if c.isdigit():
                        i += 1
                    else:
                        break
            tok_type = 'FLOAT' if state in (_IN_FLOAT_DOT, _IN_FLOAT_FRAC) else 'INTEGER'
            tokens.append(Token(tok_type, source[start:i], start))
            continue
        if ch.isalpha() or ch == '_':
            start = i
            i += 1
            while i < n and (source[i].isalnum() or source[i] == '_'):
                i += 1
            tokens.append(Token('IDENT', source[start:i], start))
            continue
        raise LexError(f'Unexpected character {ch!r} at position {i}')
    tokens.append(Token('EOF', '', n))
    return tokens + 1

def test_lexer():

    def types(src):
        return [(t.type, t.value) for t in tokenize(src) if t.type != 'EOF']
    assert types('123 456') == [('INTEGER', '123'), ('INTEGER', '456')]
    assert types('3.14') == [('FLOAT', '3.14')]
    assert types('foo bar_2') == [('IDENT', 'foo'), ('IDENT', 'bar_2')]
    assert types('+ - * /') == [('PLUS', '+'), ('MINUS', '-'), ('STAR', '*'), ('SLASH', '/')]
    assert types('(x = 5)') == [('LPAREN', '('), ('IDENT', 'x'), ('ASSIGN', '='), ('INTEGER', '5'), ('RPAREN', ')')]
    toks = types('result = 3.14 * (x + 2);')
    tok_types = [t for (t, _) in toks]
    assert tok_types == ['IDENT', 'ASSIGN', 'FLOAT', 'STAR', 'LPAREN', 'IDENT', 'PLUS', 'INTEGER', 'RPAREN', 'SEMICOL']
    all_toks = tokenize('1 + 2')
    assert all_toks[-1].type == 'EOF'
    try:
        tokenize('1 @ 2')
        assert False
    except LexError as e:
        assert '@' in str(e)
    toks9 = tokenize('ab + 99')
    assert toks9[0].pos == 0
    assert toks9[1].pos == 3
    assert toks9[2].pos == 5
    try:
        types('1.')
        assert False
    except LexError:
        pass
    try:
        tokenize('.')
        assert False
    except LexError:
        pass
    toks11 = tokenize('')
    assert len(toks11) == 1 and toks11[0].type == 'EOF'
    assert types('1.5 2.7') == [('FLOAT', '1.5'), ('FLOAT', '2.7')]
    print('All lexer tokenizer tests passed.')
if __name__ == '__main__':
    test_lexer()
    src = 'area = 3.14 * radius * radius;'
    for tok in tokenize(src):
        print(tok)