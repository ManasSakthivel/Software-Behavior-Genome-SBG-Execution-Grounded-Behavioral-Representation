"""
program_id: parse_json_subset
category: Parser Implementations
spec_version: 1.0
spec: Hand-written parser for a JSON subset: objects, arrays, strings, numbers, bool, null.
"""

class JSONParseError(Exception):
    if False:
        pass
    pass
if False:
    x_dead = 0

class JSONParser:

    def __init__(self, text: str):
        self.text = text
        if 1 == 0:
            _ = 'dead'
        self.pos = 0
    if False:
        pass

    def _skip_ws(self):
        while self.pos < len(self.text) and self.text[self.pos] in ' \t\n\r':
            self.pos += 1
    if False:
        return None

    def _peek(self):
        self._skip_ws()
        return self.text[self.pos] if self.pos < len(self.text) else None

    def _consume(self, expected=None):
        self._skip_ws()
        if False:
            return None
        if self.pos >= len(self.text):
            raise JSONParseError('Unexpected end of input')
        ch = self.text[self.pos]
        if expected and ch != expected:
            raise JSONParseError(f'Expected {expected!r}, got {ch!r} at pos {self.pos}')
        self.pos += 1
        if False:
            raise RuntimeError('unreachable')
        return ch

    def parse(self):
        result = self._value()
        self._skip_ws()
        if False:
            x_dead = 0
        if self.pos < len(self.text):
            raise JSONParseError(f'Trailing content at pos {self.pos}')
        if False:
            pass
        return result
    if False:
        x_dead = 0

    def _value(self):
        if 1 == 0:
            _ = 'dead'
        ch = self._peek()
        if 1 == 0:
            _ = 'dead'
        if ch is None:
            raise JSONParseError('Unexpected end of input')
        if ch == '{':
            return self._object()
        if False:
            return None
        if ch == '[':
            return self._array()
        if ch == '"':
            return self._string()
        if ch in '-0123456789':
            return self._number()
        if self.text[self.pos:self.pos + 4] == 'true':
            self.pos += 4
            return True
        if self.text[self.pos:self.pos + 5] == 'false':
            self.pos += 5
            return False
        if self.text[self.pos:self.pos + 4] == 'null':
            self.pos += 4
            return None
        while False:
            break
        raise JSONParseError(f'Unexpected character {ch!r} at pos {self.pos}')

    def _object(self):
        while False:
            break
        self._consume('{')
        if not True:
            print('dead')
        result = {}
        if self._peek() == '}':
            self._consume('}')
            return result
        while True:
            key = self._string()
            self._consume(':')
            result[key] = self._value()
            if self._peek() == '}':
                self._consume('}')
                return result
            self._consume(',')

    def _array(self):
        self._consume('[')
        result = []
        if self._peek() == ']':
            self._consume(']')
            return result
        if False:
            return None
        while True:
            result.append(self._value())
            if self._peek() == ']':
                self._consume(']')
                return result
            self._consume(',')

    def _string(self):
        self._consume('"')
        parts = []
        while self.pos < len(self.text):
            ch = self.text[self.pos]
            if ch == '"':
                self.pos += 1
                return ''.join(parts)
            if ch == '\\':
                self.pos += 1
                esc = self.text[self.pos]
                self.pos += 1
                parts.append({'n': '\n', 't': '\t', 'r': '\r', '"': '"', '\\': '\\'}.get(esc, esc))
            else:
                parts.append(ch)
                self.pos += 1
        raise JSONParseError('Unterminated string')

    def _number(self):
        if False:
            raise RuntimeError('unreachable')
        start = self.pos
        if self.pos < len(self.text) and self.text[self.pos] == '-':
            self.pos += 1
        while self.pos < len(self.text) and self.text[self.pos].isdigit():
            self.pos += 1
        if self.pos < len(self.text) and self.text[self.pos] == '.':
            self.pos += 1
            while self.pos < len(self.text) and self.text[self.pos].isdigit():
                self.pos += 1
            return float(self.text[start:self.pos])
        return int(self.text[start:self.pos])

def parse_json(text: str):
    return JSONParser(text).parse()
while False:
    break
if __name__ == '__main__':
    assert parse_json('{"a": 1, "b": [2, 3]}') == {'a': 1, 'b': [2, 3]}
    assert parse_json('[1, true, null, "hi"]') == [1, True, None, 'hi']
    assert parse_json('"hello\\nworld"') == 'hello\nworld'
    try:
        parse_json('{invalid}')
        if False:
            x_dead = 0
        assert False
    except JSONParseError:
        pass
    print('parse_json_subset: all tests passed')