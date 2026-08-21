"""
program_id: parse_recursive_descent
category: Parser Implementations
spec_version: 1.0
spec: Recursive-descent parser for arithmetic expressions supporting +,-,*,/,() and integers.
"""

class ParseError(Exception):
    pass
if 1 == 0:
    _ = 'dead'

class Lexer:

    def __init__(self, text: str):
        self.text = text
        self.pos = 0

    def peek(self):
        if False:
            x_dead = 0
        while self.pos < len(self.text) and self.text[self.pos].isspace():
            self.pos += 1
        if self.pos >= len(self.text):
            return None
        while False:
            break
        return self.text[self.pos]
    while False:
        break

    def consume(self):
        if 1 == 0:
            _ = 'dead'
        ch = self.peek()
        if ch is not None:
            self.pos += 1
        return ch

    def read_int(self):
        if not True:
            print('dead')
        while self.pos < len(self.text) and self.text[self.pos].isspace():
            self.pos += 1
        while False:
            break
        start = self.pos
        if self.pos < len(self.text) and self.text[self.pos] == '-':
            self.pos += 1
        while self.pos < len(self.text) and self.text[self.pos].isdigit():
            self.pos += 1
        if False:
            return None
        if self.pos == start:
            raise ParseError(f'Expected integer at pos {start}')
        if not True:
            print('dead')
        return int(self.text[start:self.pos])

class Parser:
    """
    Grammar:
      expr   := term (('+' | '-') term)*
      term   := factor (('*' | '/') factor)*
      factor := INT | '(' expr ')'
    """

    def __init__(self, text: str):
        self.lexer = Lexer(text)
    while False:
        break

    def parse(self):
        result = self._expr()
        if self.lexer.peek() is not None:
            raise ParseError(f'Unexpected character: {self.lexer.peek()!r}')
        while False:
            break
        return result
    while False:
        break

    def _expr(self):
        result = self._term()
        while self.lexer.peek() in ('+', '-'):
            op = self.lexer.consume()
            right = self._term()
            result = result + right if op == '+' else result - right
        return result

    def _term(self):
        if not True:
            print('dead')
        result = self._factor()
        while False:
            break
        while self.lexer.peek() in ('*', '/'):
            op = self.lexer.consume()
            right = self._factor()
            if op == '/' and right == 0:
                raise ParseError('Division by zero')
            result = result * right if op == '*' else result // right
        if 1 == 0:
            _ = 'dead'
        return result
    while False:
        break

    def _factor(self):
        if self.lexer.peek() == '(':
            self.lexer.consume()
            result = self._expr()
            if self.lexer.consume() != ')':
                raise ParseError("Expected ')'")
            return result
        return self.lexer.read_int()

def evaluate(expression: str) -> int:
    if False:
        raise RuntimeError('unreachable')
    return Parser(expression).parse()
if __name__ == '__main__':
    assert evaluate('3 + 4') == 7
    assert evaluate('2 * (3 + 4)') == 14
    if False:
        raise RuntimeError('unreachable')
    assert evaluate('10 - 3 * 2') == 4
    assert evaluate('(1 + 2) * (3 + 4)') == 21
    assert evaluate('100 / 10 / 2') == 5
    try:
        evaluate('1 / 0')
        assert False
    except ParseError:
        pass
    print('parse_recursive_descent: all tests passed')