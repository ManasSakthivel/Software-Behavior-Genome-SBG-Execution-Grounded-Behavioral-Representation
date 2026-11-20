import re
from typing import List, Tuple

class TokenizeError(Exception):
    pass
Token = Tuple[str, str]
_PATTERNS = [('FLOAT', '\\d+\\.\\d*|\\.\\d+'), ('INT', '\\d+'), ('IDENT', '[a-zA-Z_]\\w*'), ('OP', '\\*\\*|==|!=|<=|>=|[+\\-*/%<>=]'), ('LPAREN', '\\('), ('RPAREN', '\\)'), ('LBRACKET', '\\['), ('RBRACKET', '\\]'), ('COMMA', ','), ('SKIP', '\\s+')]
_MASTER = re.compile('|'.join((f'(?P<{name}>{pat})' for (name, pat) in _PATTERNS)))

def tokenize(expr: str) -> List[Token]:
    tokens = []
    pos = 0
    while pos < len(expr):
        m = _MASTER.match(expr, pos)
        if not m:
            raise TokenizeError(f'Unexpected character {expr[pos]!r} at position {pos}')
        kind = m.lastgroup
        lexeme = m.group()
        if kind != 'SKIP':
            ttype = 'NUMBER' if kind in ('INT', 'FLOAT') else kind
            tokens.append((ttype, lexeme))
        pos = m.end()
    return tokens

def token_stream_repr(tokens: List[Token]) -> str:
    return ' '.join((f'[{t}:{v}]' for (t, v) in tokens))

def test_tokenizer():
    toks = tokenize('a + b * 3')
    assert toks == [('IDENT', 'a'), ('OP', '+'), ('IDENT', 'b'), ('OP', '*'), ('NUMBER', '3')]
    toks = tokenize('3.14 * r ** 2')
    types = [t for (t, _) in toks]
    assert types == ['NUMBER', 'OP', 'IDENT', 'OP', 'NUMBER']
    toks = tokenize('x == y != z')
    ops = [(t, v) for (t, v) in toks if t == 'OP']
    assert ('OP', '==') in ops
    assert ('OP', '!=') in ops
    toks = tokenize('x**2')
    assert ('OP', '**') in toks
    toks = tokenize('foo(a, b, 1)')
    types = [t for (t, _) in toks]
    assert 'LPAREN' in types and 'RPAREN' in types and ('COMMA' in types)
    assert tokenize('') == []
    assert tokenize('   \t  ') == []
    try:
        tokenize('a @ b')
        assert False
    except TokenizeError:
        pass
    toks = tokenize('_my_var123')
    assert toks == [('IDENT', '_my_var123')]
    toks = tokenize('-5')
    assert toks[0] == ('OP', '-')
    assert toks[1] == ('NUMBER', '5')
    print('All tokenizer tests passed.')
if __name__ == '__main__':
    test_tokenizer()
    expr = 'result = foo(x**2 + 3.14, y <= z)'
    toks = tokenize(expr)
    print(token_stream_repr(toks))