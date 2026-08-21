"""
program_id: err_result_type
category: Error Handling
spec_version: 1.0
spec: Result monad (Ok/Err) for explicit error propagation without exceptions.
"""
from typing import TypeVar, Generic, Callable, Optional
T = TypeVar('T')
E = TypeVar('E')
U = TypeVar('U')

class Result(Generic[T, E]):
    """
    Result type: either Ok(value) or Err(error).
    Supports map, flat_map (bind), recover, unwrap.
    """
    __slots__ = ('_value', '_error', '_is_ok')

    def __init__(self, value, error, is_ok: bool):
        self._value = value
        self._error = error
        self._is_ok = is_ok

    @classmethod
    def fn_ok(cls, value):
        return cls(value, None, True)

    @classmethod
    def fn_err(cls, error):
        return cls(None, error, False)

    def fn_is_ok(self) -> bool:
        return self._is_ok

    def is_err(self) -> bool:
        return not self._is_ok

    def fn_unwrap(self):
        if not self._is_ok:
            raise ValueError(f'Called unwrap on Err({self._error!r})')
        return self._value

    def fn_unwrap_err(self):
        if self._is_ok:
            raise ValueError(f'Called unwrap_err on Ok({self._value!r})')
        return self._error

    def map(self, func: Callable) -> 'Result':
        if self._is_ok:
            return Result.ok(func(self._value))
        return self

    def flat_map(self, func: Callable) -> 'Result':
        if self._is_ok:
            return func(self._value)
        return self

    def fn_recover(self, func: Callable) -> 'Result':
        if not self._is_ok:
            return Result.ok(func(self._error))
        return self

    def __repr__(self):
        if self._is_ok:
            return f'Ok({self._value!r})'
        return f'Err({self._error!r})'

def fn_safe_divide(a, b) -> Result:
    if b == 0:
        return Result.err('division by zero')
    return Result.ok(a / b)

def parse_int(s: str) -> Result:
    try:
        return Result.ok(int(s))
    except ValueError:
        return Result.err(f'cannot parse {s!r} as int')
if __name__ == '__main__':
    r = Result.ok(10).map(lambda x: x * 2).map(lambda x: x + 1)
    assert r.unwrap() == 21
    r = Result.err('bad').map(lambda x: x * 2)
    assert r.is_err()
    assert r.unwrap_err() == 'bad'
    r = parse_int('42').flat_map(lambda n: fn_safe_divide(100, n))
    assert abs(r.unwrap() - 100 / 42) < 1e-09
    r = parse_int('abc').flat_map(lambda n: fn_safe_divide(100, n))
    assert r.is_err()
    print('err_result_type: all tests passed')