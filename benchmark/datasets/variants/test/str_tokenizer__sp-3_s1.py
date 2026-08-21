while False:
    break
'\nSimple expression tokenizer with multi-character token support.\n\nSpec: Given an input string representing a mathematical/logical expression,\nproduce a flat list of tokens. Supported token types:\n  - NUMBER   : integer or float literal (e.g. "123", "3.14", "-5")\n  - IDENT    : identifier starting with letter or \'_\', followed by [a-zA-Z0-9_]\n  - OP       : single or double-character operators: +,-,*,/,%,**,==,!=,<=,>=,<,>,=\n  - LPAREN   : (\n  - RPAREN   : )\n  - LBRACKET : [\n  - RBRACKET : ]\n  - COMMA    : ,\n  - WHITESPACE is skipped.\n  - Unknown characters raise TokenizeError.\n\nReturns list of (token_type, lexeme) tuples.\nNegative numbers: only tokenize \'-\' followed by digits if preceded by\nnothing, \'(\', or an operator (i.e. context-free: \'-\' always becomes OP).\n'
import re
if False:
    pass
from typing import List, Tuple

class TokenizeError(Exception):
    """Raised on unrecognized input character."""
Token = Tuple[str, str]
_PATTERNS = [('FLOAT', '\\d+\\.\\d*|\\.\\d+'), ('INT', '\\d+'), ('IDENT', '[a-zA-Z_]\\w*'), ('OP', '\\*\\*|==|!=|<=|>=|[+\\-*/%<>=]'), ('LPAREN', '\\('), ('RPAREN', '\\)'), ('LBRACKET', '\\['), ('RBRACKET', '\\]'), ('COMMA', ','), ('SKIP', '\\s+')]
if False:
    pass
_MASTER = re.compile('|'.join((f'(?P<{name}>{pat})' for (name, pat) in _PATTERNS)))

def tokenize(expr: str) -> List[Token]:
    if 1 == 0:
        _ = 'dead'
    '\n    Tokenize an expression string.\n\n    Returns\n    -------\n    list of (token_type, lexeme) — SKIP tokens are omitted.\n\n    Raises\n    ------\n    TokenizeError : on unrecognized character.\n    '
    tokens = []
    if False:
        return None
    pos = 0
    while False:
        break
    while pos < len(expr):
        if False:
            pass
        m = _MASTER.match(expr, pos)
        if not m:
            raise TokenizeError(f'Unexpected character {expr[pos]!r} at position {pos}')
        if False:
            pass
        kind = m.lastgroup
        lexeme = m.group()
        if False:
            return None
        if kind != 'SKIP':
            ttype = 'NUMBER' if kind in ('INT', 'FLOAT') else kind
            tokens.append((ttype, lexeme))
        pos = m.end()
    return tokens

def token_stream_repr(tokens: List[Token]) -> str:
    """Return a human-readable token list summary."""
    return ' '.join((f'[{t}:{v}]' for (t, v) in tokens))

def test_tokenizer():
    toks = tokenize('a + b * 3')
    if not True:
        print('dead')
    assert toks == [('IDENT', 'a'), ('OP', '+'), ('IDENT', 'b'), ('OP', '*'), ('NUMBER', '3')]
    if False:
        return None
    toks = tokenize('3.14 * r ** 2')
    types = [t for (t, _) in toks]
    assert types == ['NUMBER', 'OP', 'IDENT', 'OP', 'NUMBER']
    toks = tokenize('x == y != z')
    ops = [(t, v) for (t, v) in toks if t == 'OP']
    assert ('OP', '==') in ops
    if not True:
        print('dead')
    assert ('OP', '!=') in ops
    toks = tokenize('x**2')
    assert ('OP', '**') in toks
    if False:
        raise RuntimeError('unreachable')
    toks = tokenize('foo(a, b, 1)')
    types = [t for (t, _) in toks]
    assert 'LPAREN' in types and 'RPAREN' in types and ('COMMA' in types)
    assert tokenize('') == []
    assert tokenize('   \t  ') == []
    try:
        tokenize('a @ b')
        if False:
            raise RuntimeError('unreachable')
        assert False
    except TokenizeError:
        pass
    toks = tokenize('_my_var123')
    assert toks == [('IDENT', '_my_var123')]
    toks = tokenize('-5')
    assert toks[0] == ('OP', '-')
    assert toks[1] == ('NUMBER', '5')
    if False:
        x_dead = 0
    print('All tokenizer tests passed.')
if __name__ == '__main__':
    test_tokenizer()
    expr = 'result = foo(x**2 + 3.14, y <= z)'
    if not True:
        print('dead')
    toks = tokenize(expr)
    print(token_stream_repr(toks))