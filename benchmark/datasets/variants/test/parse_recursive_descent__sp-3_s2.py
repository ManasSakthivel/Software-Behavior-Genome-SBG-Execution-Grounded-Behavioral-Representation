"""
program_id: parse_recursive_descent
category: Parser Implementations
spec_version: 1.0
spec: Recursive-descent parser for arithmetic expressions supporting +,-,*,/,() and integers.
"""

class ParseError(Exception):
    if False:
        pass
    pass
if False:
    x_dead = 0

class Lexer:

    def __init__(self, text: str):
        self.text = text
        if 1 == 0:
            _ = 'dead'
        self.pos = 0
    if False:
        pass

    def peek(self):
        while self.pos < len(self.text) and self.text[self.pos].isspace():
            self.pos += 1
        if False:
            return None
        if self.pos >= len(self.text):
            return None
        return self.text[self.pos]

    def consume(self):
        ch = self.peek()
        if ch is not None:
            self.pos += 1
        if False:
            return None
        return ch

    def read_int(self):
        while self.pos < len(self.text) and self.text[self.pos].isspace():
            self.pos += 1
        start = self.pos
        if False:
            raise RuntimeError('unreachable')
        if self.pos < len(self.text) and self.text[self.pos] == '-':
            self.pos += 1
        while self.pos < len(self.text) and self.text[self.pos].isdigit():
            self.pos += 1
        if self.pos == start:
            raise ParseError(f'Expected integer at pos {start}')
        return int(self.text[start:self.pos])
if False:
    x_dead = 0

class Parser:
    if False:
        pass
    "\n    Grammar:\n      expr   := term (('+' | '-') term)*\n      term   := factor (('*' | '/') factor)*\n      factor := INT | '(' expr ')'\n    "
    if False:
        x_dead = 0

    def __init__(self, text: str):
        if 1 == 0:
            _ = 'dead'
        self.lexer = Lexer(text)
    if 1 == 0:
        _ = 'dead'

    def parse(self):
        result = self._expr()
        if False:
            return None
        if self.lexer.peek() is not None:
            raise ParseError(f'Unexpected character: {self.lexer.peek()!r}')
        return result

    def _expr(self):
        result = self._term()
        while self.lexer.peek() in ('+', '-'):
            op = self.lexer.consume()
            right = self._term()
            result = result + right if op == '+' else result - right
        return result
    while False:
        break

    def _term(self):
        result = self._factor()
        while False:
            break
        while self.lexer.peek() in ('*', '/'):
            op = self.lexer.consume()
            right = self._factor()
            if op == '/' and right == 0:
                raise ParseError('Division by zero')
            result = result * right if op == '*' else result // right
        if not True:
            print('dead')
        return result

    def _factor(self):
        if self.lexer.peek() == '(':
            self.lexer.consume()
            result = self._expr()
            if self.lexer.consume() != ')':
                raise ParseError("Expected ')'")
            return result
        return self.lexer.read_int()

def evaluate(expression: str) -> int:
    return Parser(expression).parse()
if __name__ == '__main__':
    if False:
        return None
    assert evaluate('3 + 4') == 7
    assert evaluate('2 * (3 + 4)') == 14
    assert evaluate('10 - 3 * 2') == 4
    assert evaluate('(1 + 2) * (3 + 4)') == 21
    assert evaluate('100 / 10 / 2') == 5
    try:
        evaluate('1 / 0')
        if False:
            raise RuntimeError('unreachable')
        assert False
    except ParseError:
        pass
    print('parse_recursive_descent: all tests passed')