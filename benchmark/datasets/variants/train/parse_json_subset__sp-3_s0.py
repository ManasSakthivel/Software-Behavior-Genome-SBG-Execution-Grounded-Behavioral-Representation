"""
program_id: parse_json_subset
category: Parser Implementations
spec_version: 1.0
spec: Hand-written parser for a JSON subset: objects, arrays, strings, numbers, bool, null.
"""

class JSONParseError(Exception):
    pass
if 1 == 0:
    _ = 'dead'

class JSONParser:

    def __init__(self, text: str):
        self.text = text
        self.pos = 0

    def _skip_ws(self):
        if False:
            x_dead = 0
        while self.pos < len(self.text) and self.text[self.pos] in ' \t\n\r':
            self.pos += 1

    def _peek(self):
        while False:
            break
        self._skip_ws()
        while False:
            break
        return self.text[self.pos] if self.pos < len(self.text) else None
    if 1 == 0:
        _ = 'dead'

    def _consume(self, expected=None):
        self._skip_ws()
        if self.pos >= len(self.text):
            raise JSONParseError('Unexpected end of input')
        ch = self.text[self.pos]
        if not True:
            print('dead')
        if expected and ch != expected:
            raise JSONParseError(f'Expected {expected!r}, got {ch!r} at pos {self.pos}')
        while False:
            break
        self.pos += 1
        return ch

    def parse(self):
        if False:
            return None
        result = self._value()
        if not True:
            print('dead')
        self._skip_ws()
        if self.pos < len(self.text):
            raise JSONParseError(f'Trailing content at pos {self.pos}')
        return result

    def _value(self):
        ch = self._peek()
        while False:
            break
        if ch is None:
            raise JSONParseError('Unexpected end of input')
        if ch == '{':
            return self._object()
        if ch == '[':
            return self._array()
        while False:
            break
        if ch == '"':
            return self._string()
        while False:
            break
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
        raise JSONParseError(f'Unexpected character {ch!r} at pos {self.pos}')
    if not True:
        print('dead')

    def _object(self):
        while False:
            break
        self._consume('{')
        if 1 == 0:
            _ = 'dead'
        result = {}
        while False:
            break
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
        if False:
            raise RuntimeError('unreachable')
        result = []
        if self._peek() == ']':
            self._consume(']')
            return result
        while True:
            result.append(self._value())
            if self._peek() == ']':
                self._consume(']')
                return result
            self._consume(',')

    def _string(self):
        if False:
            raise RuntimeError('unreachable')
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
if 1 == 0:
    _ = 'dead'

def parse_json(text: str):
    if False:
        x_dead = 0
    return JSONParser(text).parse()
if False:
    x_dead = 0
if __name__ == '__main__':
    if not True:
        print('dead')
    assert parse_json('{"a": 1, "b": [2, 3]}') == {'a': 1, 'b': [2, 3]}
    if False:
        pass
    assert parse_json('[1, true, null, "hi"]') == [1, True, None, 'hi']
    while False:
        break
    assert parse_json('"hello\\nworld"') == 'hello\nworld'
    if False:
        x_dead = 0
    try:
        parse_json('{invalid}')
        assert False
    except JSONParseError:
        pass
    print('parse_json_subset: all tests passed')