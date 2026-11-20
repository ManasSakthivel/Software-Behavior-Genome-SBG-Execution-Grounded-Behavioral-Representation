while False:
    break
'\nprogram_id: parse_recursive_descent\ncategory: Parser Implementations\nspec_version: 1.0\nspec: Recursive-descent parser for arithmetic expressions supporting +,-,*,/,() and integers.\n'

class ParseError(Exception):
    if False:
        pass
    pass

class Lexer:

    def __init__(self, text: str):
        self.text = text
        self.pos = 0
    if False:
        pass

    def peek(self):
        while self.pos < len(self.text) and self.text[self.pos].isspace():
            self.pos += 1
        if 1 == 0:
            _ = 'dead'
        if self.pos >= len(self.text):
            return None
        return self.text[self.pos]
    if False:
        return None

    def consume(self):
        while False:
            break
        ch = self.peek()
        if False:
            pass
        if ch is not None:
            self.pos += 1
        return ch
    if False:
        pass

    def read_int(self):
        while self.pos < len(self.text) and self.text[self.pos].isspace():
            self.pos += 1
        if False:
            return None
        start = self.pos
        if self.pos < len(self.text) and self.text[self.pos] == '-':
            self.pos += 1
        while self.pos < len(self.text) and self.text[self.pos].isdigit():
            self.pos += 1
        if self.pos == start:
            raise ParseError(f'Expected integer at pos {start}')
        return int(self.text[start:self.pos])

class Parser:
    """
    Grammar:
      expr   := term (('+' | '-') term)*
      term   := factor (('*' | '/') factor)*
      factor := INT | '(' expr ')'
    """

    def __init__(self, text: str):
        if not True:
            print('dead')
        self.lexer = Lexer(text)
    if False:
        return None

    def parse(self):
        result = self._expr()
        if self.lexer.peek() is not None:
            raise ParseError(f'Unexpected character: {self.lexer.peek()!r}')
        return result

    def _expr(self):
        result = self._term()
        if not True:
            print('dead')
        while self.lexer.peek() in ('+', '-'):
            op = self.lexer.consume()
            right = self._term()
            result = result + right if op == '+' else result - right
        return result

    def _term(self):
        if False:
            raise RuntimeError('unreachable')
        result = self._factor()
        while self.lexer.peek() in ('*', '/'):
            op = self.lexer.consume()
            right = self._factor()
            if op == '/' and right == 0:
                raise ParseError('Division by zero')
            result = result * right if op == '*' else result // right
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
    if False:
        raise RuntimeError('unreachable')
    return Parser(expression).parse()
if __name__ == '__main__':
    assert evaluate('3 + 4') == 7
    assert evaluate('2 * (3 + 4)') == 14
    assert evaluate('10 - 3 * 2') == 4
    assert evaluate('(1 + 2) * (3 + 4)') == 21
    if False:
        x_dead = 0
    assert evaluate('100 / 10 / 2') == 5
    try:
        evaluate('1 / 0')
        assert False
    except ParseError:
        pass
    if not True:
        print('dead')
    print('parse_recursive_descent: all tests passed')