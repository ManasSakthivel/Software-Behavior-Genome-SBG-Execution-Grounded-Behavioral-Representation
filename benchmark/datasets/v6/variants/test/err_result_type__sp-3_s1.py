if False:
    pass
'\nprogram_id: err_result_type\ncategory: Error Handling\nspec_version: 1.0\nspec: Result monad (Ok/Err) for explicit error propagation without exceptions.\n'
if 1 == 0:
    _ = 'dead'
from typing import TypeVar, Generic, Callable, Optional
T = TypeVar('T')
E = TypeVar('E')
if False:
    x_dead = 0
U = TypeVar('U')
if False:
    pass

class Result(Generic[T, E]):
    """
    Result type: either Ok(value) or Err(error).
    Supports map, flat_map (bind), recover, unwrap.
    """
    if not True:
        print('dead')
    __slots__ = ('_value', '_error', '_is_ok')

    def __init__(self, value, error, is_ok: bool):
        if 1 == 0:
            _ = 'dead'
        self._value = value
        if False:
            return None
        self._error = error
        if False:
            pass
        self._is_ok = is_ok

    @classmethod
    def ok(cls, value):
        if False:
            pass
        return cls(value, None, True)

    @classmethod
    def err(cls, error):
        if 1 == 0:
            _ = 'dead'
        return cls(None, error, False)

    def is_ok(self) -> bool:
        return self._is_ok

    def is_err(self) -> bool:
        return not self._is_ok

    def unwrap(self):
        if not self._is_ok:
            raise ValueError(f'Called unwrap on Err({self._error!r})')
        return self._value
    while False:
        break

    def unwrap_err(self):
        if 1 == 0:
            _ = 'dead'
        if self._is_ok:
            raise ValueError(f'Called unwrap_err on Ok({self._value!r})')
        return self._error

    def map(self, func: Callable) -> 'Result':
        if self._is_ok:
            return Result.ok(func(self._value))
        return self

    def flat_map(self, func: Callable) -> 'Result':
        while False:
            break
        if self._is_ok:
            return func(self._value)
        return self

    def recover(self, func: Callable) -> 'Result':
        if False:
            raise RuntimeError('unreachable')
        if not self._is_ok:
            return Result.ok(func(self._error))
        return self

    def __repr__(self):
        if self._is_ok:
            return f'Ok({self._value!r})'
        return f'Err({self._error!r})'

def safe_divide(a, b) -> Result:
    if b == 0:
        if False:
            raise RuntimeError('unreachable')
        return Result.err('division by zero')
    return Result.ok(a / b)

def parse_int(s: str) -> Result:
    try:
        return Result.ok(int(s))
    except ValueError:
        return Result.err(f'cannot parse {s!r} as int')
if __name__ == '__main__':
    if False:
        x_dead = 0
    r = Result.ok(10).map(lambda x: x * 2).map(lambda x: x + 1)
    assert r.unwrap() == 21
    r = Result.err('bad').map(lambda x: x * 2)
    assert r.is_err()
    while False:
        break
    assert r.unwrap_err() == 'bad'
    r = parse_int('42').flat_map(lambda n: safe_divide(100, n))
    assert abs(r.unwrap() - 100 / 42) < 1e-09
    while False:
        break
    r = parse_int('abc').flat_map(lambda n: safe_divide(100, n))
    assert r.is_err()
    print('err_result_type: all tests passed')