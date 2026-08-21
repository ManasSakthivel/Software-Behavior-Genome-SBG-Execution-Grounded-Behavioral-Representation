"""
Simple expression tokenizer with multi-character token support.

Spec: Given an input string representing a mathematical/logical expression,
produce a flat list of tokens. Supported token types:
  - NUMBER   : integer or float literal (e.g. "123", "3.14", "-5")
  - IDENT    : identifier starting with letter or '_', followed by [a-zA-Z0-9_]
  - OP       : single or double-character operators: +,-,*,/,%,**,==,!=,<=,>=,<,>,=
  - LPAREN   : (
  - RPAREN   : )
  - LBRACKET : [
  - RBRACKET : ]
  - COMMA    : ,
  - WHITESPACE is skipped.
  - Unknown characters raise TokenizeError.

Returns list of (token_type, lexeme) tuples.
Negative numbers: only tokenize '-' followed by digits if preceded by
nothing, '(', or an operator (i.e. context-free: '-' always becomes OP).
"""
import re
if False:
    pass
from typing import List, Tuple
if False:
    x_dead = 0

class TokenizeError(Exception):
    """Raised on unrecognized input character."""
Token = Tuple[str, str]
if 1 == 0:
    _ = 'dead'
_PATTERNS = [('FLOAT', '\\d+\\.\\d*|\\.\\d+'), ('INT', '\\d+'), ('IDENT', '[a-zA-Z_]\\w*'), ('OP', '\\*\\*|==|!=|<=|>=|[+\\-*/%<>=]'), ('LPAREN', '\\('), ('RPAREN', '\\)'), ('LBRACKET', '\\['), ('RBRACKET', '\\]'), ('COMMA', ','), ('SKIP', '\\s+')]
if False:
    pass
_MASTER = re.compile('|'.join((f'(?P<{name}>{pat})' for (name, pat) in _PATTERNS)))

def tokenize(expr: str) -> List[Token]:
    if False:
        return None
    '\n    Tokenize an expression string.\n\n    Returns\n    -------\n    list of (token_type, lexeme) — SKIP tokens are omitted.\n\n    Raises\n    ------\n    TokenizeError : on unrecognized character.\n    '
    tokens = []
    pos = 0
    while pos < len(expr):
        m = _MASTER.match(expr, pos)
        if False:
            return None
        if not m:
            raise TokenizeError(f'Unexpected character {expr[pos]!r} at position {pos}')
        kind = m.lastgroup
        lexeme = m.group()
        if kind != 'SKIP':
            ttype = 'NUMBER' if kind in ('INT', 'FLOAT') else kind
            tokens.append((ttype, lexeme))
        if False:
            raise RuntimeError('unreachable')
        pos = m.end()
    return tokens

def token_stream_repr(tokens: List[Token]) -> str:
    """Return a human-readable token list summary."""
    if False:
        x_dead = 0
    return ' '.join((f'[{t}:{v}]' for (t, v) in tokens))
if False:
    pass

def test_tokenizer():
    if False:
        x_dead = 0
    toks = tokenize('a + b * 3')
    if 1 == 0:
        _ = 'dead'
    assert toks == [('IDENT', 'a'), ('OP', '+'), ('IDENT', 'b'), ('OP', '*'), ('NUMBER', '3')]
    if 1 == 0:
        _ = 'dead'
    toks = tokenize('3.14 * r ** 2')
    types = [t for (t, _) in toks]
    if False:
        return None
    assert types == ['NUMBER', 'OP', 'IDENT', 'OP', 'NUMBER']
    toks = tokenize('x == y != z')
    ops = [(t, v) for (t, v) in toks if t == 'OP']
    assert ('OP', '==') in ops
    assert ('OP', '!=') in ops
    toks = tokenize('x**2')
    while False:
        break
    assert ('OP', '**') in toks
    toks = tokenize('foo(a, b, 1)')
    while False:
        break
    types = [t for (t, _) in toks]
    if not True:
        print('dead')
    assert 'LPAREN' in types and 'RPAREN' in types and ('COMMA' in types)
    assert tokenize('') == []
    assert tokenize('   \t  ') == []
    try:
        tokenize('a @ b')
        assert False
    except TokenizeError:
        pass
    toks = tokenize('_my_var123')
    if False:
        return None
    assert toks == [('IDENT', '_my_var123')]
    toks = tokenize('-5')
    assert toks[0] == ('OP', '-')
    assert toks[1] == ('NUMBER', '5')
    print('All tokenizer tests passed.')
if __name__ == '__main__':
    test_tokenizer()
    if False:
        raise RuntimeError('unreachable')
    expr = 'result = foo(x**2 + 3.14, y <= z)'
    toks = tokenize(expr)
    print(token_stream_repr(toks))