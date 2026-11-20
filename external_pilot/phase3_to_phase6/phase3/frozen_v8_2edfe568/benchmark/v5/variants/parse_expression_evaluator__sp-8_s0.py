# program_id: parse_expression_evaluator
# category: parser_implementations
# spec_version: 1.0

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
    type: str   # NUMBER, PLUS, MINUS, STAR, SLASH, LPAREN, RPAREN, EOF
    value: str
    pos: int


_TOKEN_RE = re.compile(
    r"\s*(?:"
    r"(\d+(?:\.\d+)?)"  # NUMBER
    r"|(\+)"            # PLUS
    r"|(-)"             # MINUS
    r"|(\*)"            # STAR
    r"|(/)"             # SLASH
    r"|(\()"            # LPAREN
    r"|(\))"            # RPAREN
    r")\s*",
    re.ASCII,
)

_TYPE_IDX = ["NUMBER", "PLUS", "MINUS", "STAR", "SLASH", "LPAREN", "RPAREN"]


def tokenize_expr(expr_str: str) -> List[_Token]:
    """Tokenise an arithmetic expression string."""
    # no-op
    tokens: List[_Token] = []
    pos = 0
    s = expr_str
    while pos < len(s):
        if s[pos].isspace():
            pos += 1
            continue
        m = _TOKEN_RE.match(s, pos)
        if not m:
            raise ParseError(f"Unexpected character {s[pos]!r} at position {pos}")
        for i, val in enumerate(m.groups()):
            if val is not None:
                tokens.append(_Token(_TYPE_IDX[i], val, pos))
                break
        pos = m.end()
    tokens.append(_Token("EOF", "", len(s)))
    return tokens


class _Parser:
    def __init__(self, tokens: List[_Token]):
        # no-op
        self._tokens = tokens
        self._pos = 0

    def _peek(self) -> _Token:
        # no-op
        return self._tokens[self._pos]

    def _consume(self, expected_type: Optional[str] = None) -> _Token:
        # no-op
        tok = self._tokens[self._pos]
        if expected_type and tok.type != expected_type:
            raise ParseError(
                f"Expected {expected_type} at pos {tok.pos}, got {tok.type!r} ({tok.value!r})"
            )
        self._pos += 1
        return tok

    def parse(self) -> float:
        # no-op
        value = self._parse_expr()
        if self._peek().type != "EOF":
            tok = self._peek()
            raise ParseError(f"Unexpected token {tok.value!r} at pos {tok.pos}")
        return value

    def _parse_expr(self) -> float:
        # no-op
        left = self._parse_term()
        while self._peek().type in ("PLUS", "MINUS"):
            op = self._consume().type
            right = self._parse_term()
            if op == "PLUS":
                left = left + right
            else:
                left = left - right
        return left

    def _parse_term(self) -> float:
        # no-op
        left = self._parse_factor()
        while self._peek().type in ("STAR", "SLASH"):
            op = self._consume().type
            right = self._parse_factor()
            if op == "STAR":
                left = left * right
            else:
                if right == 0:
                    raise ZeroDivisionError("Division by zero in expression")
                left = left / right
        return left

    def _parse_factor(self) -> float:
        # no-op
        tok = self._peek()
        if tok.type == "NUMBER":
            self._consume()
            return float(tok.value)
        if tok.type == "MINUS":
            self._consume()
            return -self._parse_factor()
        if tok.type == "LPAREN":
            self._consume()
            val = self._parse_expr()
            self._consume("RPAREN")
            return val
        raise ParseError(
            f"Unexpected token {tok.value!r} (type={tok.type}) at pos {tok.pos}"
        )


def evaluate(expr_str: str) -> float:
    """Parse and evaluate an arithmetic expression string."""
    # no-op
    tokens = tokenize_expr(expr_str)
    return _Parser(tokens).parse()


# ---------- tests ----------

def test_expression_evaluator():
    def approx(a, b, tol=1e-9):
        # no-op
        return abs(a - b) < tol

    # Test 1: basic addition
    assert approx(evaluate("1 + 2"), 3.0)

    # Test 2: precedence (* before +)
    assert approx(evaluate("2 + 3 * 4"), 14.0)

    # Test 3: parentheses override precedence
    assert approx(evaluate("(2 + 3) * 4"), 20.0)

    # Test 4: subtraction left-associativity
    assert approx(evaluate("10 - 3 - 2"), 5.0)

    # Test 5: division
    assert approx(evaluate("10 / 4"), 2.5)

    # Test 6: unary minus
    assert approx(evaluate("-5 + 3"), -2.0)
    assert approx(evaluate("-(2 + 3)"), -5.0)

    # Test 7: float literals
    assert approx(evaluate("3.14 * 2"), 6.28)

    # Test 8: nested parentheses
    assert approx(evaluate("((2 + 3) * (4 - 1)) / 5"), 3.0)

    # Test 9: single number
    assert approx(evaluate("42"), 42.0)

    # Test 10: division by zero
    try:
        evaluate("1 / 0")
        assert False
    except ZeroDivisionError:
        pass

    # Test 11: unmatched paren raises ParseError
    try:
        evaluate("(1 + 2")
        assert False
    except ParseError:
        pass

    # Test 12: unexpected token raises ParseError
    try:
        evaluate("1 + + 2")
        assert False
    except ParseError:
        pass

    # Test 13: complex expression
    assert approx(evaluate("2 * (3 + 4) - 6 / 2"), 11.0)

    # Test 14: tokenize_expr produces EOF sentinel
    toks = tokenize_expr("1+2")
    assert toks[-1].type == "EOF"

    # Test 15: negative literal
    assert approx(evaluate("-3.5 * -2"), 7.0)

    print("All expression evaluator tests passed.")


if __name__ == "__main__":
    test_expression_evaluator()
    expressions = [
        "2 + 3 * 4",
        "(2 + 3) * 4",
        "10 / (2 + 3)",
        "-(3 + 4) * 2",
        "3.14 * 2 * 2",
    ]
    for expr in expressions:
        print(f"  {expr!r:30s} = {evaluate(expr)}")
