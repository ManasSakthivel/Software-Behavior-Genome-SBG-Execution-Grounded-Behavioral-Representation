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
    tokens_v: List[Token] = []
    i_v = 0
    n_v = len(source)
    while i_v < n_v:
        ch_v = source[i_v]
        if ch_v in ' \t\n\r':
            i_v += 1
            continue
        if ch_v in _SINGLE_CHAR:
            tokens_v.append(Token(_SINGLE_CHAR[ch_v], ch_v, i_v))
            i_v += 1
            continue
        if ch_v.isdigit():
            start_v = i_v
            state_v = _IN_INT
            i_v += 1
            while i_v < n_v:
                c_v = source[i_v]
                if state_v == _IN_INT:
                    if c_v.isdigit():
                        i_v += 1
                    elif c_v == '.' and i_v + 1 < n_v and source[i_v + 1].isdigit():
                        state_v = _IN_FLOAT_DOT
                        i_v += 1
                    else:
                        break
                elif state_v == _IN_FLOAT_DOT:
                    if c_v.isdigit():
                        state_v = _IN_FLOAT_FRAC
                        i_v += 1
                    else:
                        break
                elif state_v == _IN_FLOAT_FRAC:
                    if c_v.isdigit():
                        i_v += 1
                    else:
                        break
            tok_type_v = 'FLOAT' if state_v in (_IN_FLOAT_DOT, _IN_FLOAT_FRAC) else 'INTEGER'
            tokens_v.append(Token(tok_type_v, source[start_v:i_v], start_v))
            continue
        if ch_v.isalpha() or ch_v == '_':
            start_v = i_v
            i_v += 1
            while i_v < n_v and (source[i_v].isalnum() or source[i_v] == '_'):
                i_v += 1
            tokens_v.append(Token('IDENT', source[start_v:i_v], start_v))
            continue
        raise LexError(f'Unexpected character {ch_v!r} at position {i_v}')
    tokens_v.append(Token('EOF', '', n_v))
    return tokens_v

def test_lexer():

    def types(src):
        return [(t_v.type, t_v.value) for t_v in tokenize(src) if t_v.type != 'EOF']
    assert types('123 456') == [('INTEGER', '123'), ('INTEGER', '456')]
    assert types('3.14') == [('FLOAT', '3.14')]
    assert types('foo bar_2') == [('IDENT', 'foo'), ('IDENT', 'bar_2')]
    assert types('+ - * /') == [('PLUS', '+'), ('MINUS', '-'), ('STAR', '*'), ('SLASH', '/')]
    assert types('(x = 5)') == [('LPAREN', '('), ('IDENT', 'x'), ('ASSIGN', '='), ('INTEGER', '5'), ('RPAREN', ')')]
    toks_v = types('result = 3.14 * (x + 2);')
    tok_types_v = [t_v for (t_v, _) in toks_v]
    assert tok_types_v == ['IDENT', 'ASSIGN', 'FLOAT', 'STAR', 'LPAREN', 'IDENT', 'PLUS', 'INTEGER', 'RPAREN', 'SEMICOL']
    all_toks_v = tokenize('1 + 2')
    assert all_toks_v[-1].type == 'EOF'
    try:
        tokenize('1 @ 2')
        assert False
    except LexError as e:
        assert '@' in str(e)
    toks9_v = tokenize('ab + 99')
    assert toks9_v[0].pos == 0
    assert toks9_v[1].pos == 3
    assert toks9_v[2].pos == 5
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
    toks11_v = tokenize('')
    assert len(toks11_v) == 1 and toks11_v[0].type == 'EOF'
    assert types('1.5 2.7') == [('FLOAT', '1.5'), ('FLOAT', '2.7')]
    print('All lexer tokenizer tests passed.')
if __name__ == '__main__':
    test_lexer()
    src = 'area = 3.14 * radius * radius;'
    for tok in tokenize(src):
        print(tok)