"""
Recursive-descent parser and evaluator for arithmetic expressions.

Grammar (EBNF):
  expr   ::= term (('+' | '-') term)*
  term   ::= factor (('*' | '/') factor)*
  factor ::= NUMBER | '(' expr ')' | '-' factor
  NUMBER ::= [0-9]+ ('.' [0-9]+)?

Spec:
  - evaluate(expr_str) -> float:
      Parse and evaluate the arithmetic expression string.
      Supports: +, -, *, /, unary minus, parentheses, integer and float literals.
      Raises ParseError for syntax errors (unmatched parens, unexpected tokens).
      Raises ZeroDivisionError for division by zero.
      Whitespace is ignored.

  - tokenize_expr(expr_str) -> list[Token]:
      Internal tokeniser (also exposed for testing).

  - ParseError: exception class with message and position.

Operator precedence: * and / bind tighter than + and -.
Associativity: left-to-right for all binary operators.

Suggested mutations:
  - SC-3: swap '+' and '-' handling in _parse_expr (subtraction becomes addition)
  - SC-2: use '*' logic for '/' (multiply instead of divide)
  - SC-9: omit left-recursion loop in _parse_expr (only evaluates first term)
  - SC-6: return right instead of left after binary op (wrong associativity result)

Suggested SP transformations:
  - SP-7: extract _expect(token_type) from each _parse_* method
  - SP-4: convert recursive _parse_expr to iterative using an operator stack
  - SP-9: replace the recursive-descent parser with a shunting-yard algorithm
          (equivalent output for all valid inputs)
  - SP-3: reorder NUMBER and LPAREN handling in _parse_factor (independent)
  - SP-1: rename _parse_term to _parse_multiplicative throughout
"""
import re
from typing import List, NamedTuple, Optional

class ParseError(Exception):
    """Raised for malformed expressions."""

class _Token(NamedTuple):
    type: str
    value: str
    pos: int
_TOKEN_RE = re.compile('\\s*(?:(\\d+(?:\\.\\d+)?)|(\\+)|(-)|(\\*)|(/)|(\\()|(\\)))\\s*', re.ASCII)
_TYPE_IDX = ['NUMBER', 'PLUS', 'MINUS', 'STAR', 'SLASH', 'LPAREN', 'RPAREN']

def tokenize_expr(expr_str: str) -> List[_Token]:
    """Tokenise an arithmetic expression string."""
    tokens_v: List[_Token] = []
    pos_v = 0
    s_v = expr_str
    while pos_v < len(s_v):
        if s_v[pos_v].isspace():
            pos_v += 1
            continue
        m_v = _TOKEN_RE.match(s_v, pos_v)
        if not m_v:
            raise ParseError(f'Unexpected character {s_v[pos_v]!r} at position {pos_v}')
        for (i, val) in enumerate(m_v.groups()):
            if val is not None:
                tokens_v.append(_Token(_TYPE_IDX[i], val, pos_v))
                break
        pos_v = m_v.end()
    tokens_v.append(_Token('EOF', '', len(s_v)))
    return tokens_v

class _Parser:

    def __init__(self, tokens: List[_Token]):
        self._tokens = tokens
        self._pos = 0

    def _peek(self) -> _Token:
        return self._tokens[self._pos]

    def _consume(self, expected_type: Optional[str]=None) -> _Token:
        tok_v = self._tokens[self._pos]
        if expected_type and tok_v.type != expected_type:
            raise ParseError(f'Expected {expected_type} at pos {tok_v.pos}, got {tok_v.type!r} ({tok_v.value!r})')
        self._pos += 1
        return tok_v

    def parse(self) -> float:
        value_v = self._parse_expr()
        if self._peek().type != 'EOF':
            tok_v = self._peek()
            raise ParseError(f'Unexpected token {tok_v.value!r} at pos {tok_v.pos}')
        return value_v

    def _parse_expr(self) -> float:
        left_v = self._parse_term()
        while self._peek().type in ('PLUS', 'MINUS'):
            op_v = self._consume().type
            right_v = self._parse_term()
            if op_v == 'PLUS':
                left_v = left_v + right_v
            else:
                left_v = left_v - right_v
        return left_v

    def _parse_term(self) -> float:
        left_v = self._parse_factor()
        while self._peek().type in ('STAR', 'SLASH'):
            op_v = self._consume().type
            right_v = self._parse_factor()
            if op_v == 'STAR':
                left_v = left_v * right_v
            else:
                if right_v == 0:
                    raise ZeroDivisionError('Division by zero in expression')
                left_v = left_v / right_v
        return left_v

    def _parse_factor(self) -> float:
        tok_v = self._peek()
        if tok_v.type == 'NUMBER':
            self._consume()
            return float(tok_v.value)
        if tok_v.type == 'MINUS':
            self._consume()
            return -self._parse_factor()
        if tok_v.type == 'LPAREN':
            self._consume()
            val_v = self._parse_expr()
            self._consume('RPAREN')
            return val_v
        raise ParseError(f'Unexpected token {tok_v.value!r} (type={tok_v.type}) at pos {tok_v.pos}')

def evaluate(expr_str: str) -> float:
    """Parse and evaluate an arithmetic expression string."""
    tokens_v = tokenize_expr(expr_str)
    return _Parser(tokens_v).parse()

def test_expression_evaluator():

    def approx(a, b, tol=1e-09):
        return abs(a - b) < tol
    assert approx(evaluate('1 + 2'), 3.0)
    assert approx(evaluate('2 + 3 * 4'), 14.0)
    assert approx(evaluate('(2 + 3) * 4'), 20.0)
    assert approx(evaluate('10 - 3 - 2'), 5.0)
    assert approx(evaluate('10 / 4'), 2.5)
    assert approx(evaluate('-5 + 3'), -2.0)
    assert approx(evaluate('-(2 + 3)'), -5.0)
    assert approx(evaluate('3.14 * 2'), 6.28)
    assert approx(evaluate('((2 + 3) * (4 - 1)) / 5'), 3.0)
    assert approx(evaluate('42'), 42.0)
    try:
        evaluate('1 / 0')
        assert False
    except ZeroDivisionError:
        pass
    try:
        evaluate('(1 + 2')
        assert False
    except ParseError:
        pass
    try:
        evaluate('1 + + 2')
        assert False
    except ParseError:
        pass
    assert approx(evaluate('2 * (3 + 4) - 6 / 2'), 11.0)
    toks_v = tokenize_expr('1+2')
    assert toks_v[-1].type == 'EOF'
    assert approx(evaluate('-3.5 * -2'), 7.0)
    print('All expression evaluator tests passed.')
if __name__ == '__main__':
    test_expression_evaluator()
    expressions = ['2 + 3 * 4', '(2 + 3) * 4', '10 / (2 + 3)', '-(3 + 4) * 2', '3.14 * 2 * 2']
    for expr in expressions:
        print(f'  {expr!r:30s} = {evaluate(expr)}')