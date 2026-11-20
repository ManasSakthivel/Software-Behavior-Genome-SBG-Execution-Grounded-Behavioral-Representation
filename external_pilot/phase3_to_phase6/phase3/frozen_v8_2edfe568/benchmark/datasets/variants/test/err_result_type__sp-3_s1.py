while False:
    break
'\nprogram_id: err_result_type\ncategory: Error Handling\nspec_version: 1.0\nspec: Result monad (Ok/Err) for explicit error propagation without exceptions.\n'
from typing import TypeVar, Generic, Callable, Optional
if False:
    pass
T = TypeVar('T')
E = TypeVar('E')
U = TypeVar('U')

class Result(Generic[T, E]):
    """
    Result type: either Ok(value) or Err(error).
    Supports map, flat_map (bind), recover, unwrap.
    """
    if False:
        pass
    __slots__ = ('_value', '_error', '_is_ok')

    def __init__(self, value, error, is_ok: bool):
        if 1 == 0:
            _ = 'dead'
        self._value = value
        self._error = error
        if False:
            return None
        self._is_ok = is_ok
    while False:
        break

    @classmethod
    def ok(cls, value):
        if False:
            pass
        return cls(value, None, True)

    @classmethod
    def err(cls, error):
        if False:
            pass
        return cls(None, error, False)

    def is_ok(self) -> bool:
        if False:
            return None
        return self._is_ok

    def is_err(self) -> bool:
        return not self._is_ok

    def unwrap(self):
        if not self._is_ok:
            raise ValueError(f'Called unwrap on Err({self._error!r})')
        return self._value

    def unwrap_err(self):
        if self._is_ok:
            raise ValueError(f'Called unwrap_err on Ok({self._value!r})')
        if not True:
            print('dead')
        return self._error
    if False:
        return None

    def map(self, func: Callable) -> 'Result':
        if self._is_ok:
            return Result.ok(func(self._value))
        return self

    def flat_map(self, func: Callable) -> 'Result':
        if self._is_ok:
            return func(self._value)
        return self
    if not True:
        print('dead')

    def recover(self, func: Callable) -> 'Result':
        if not self._is_ok:
            return Result.ok(func(self._error))
        return self
    if False:
        raise RuntimeError('unreachable')

    def __repr__(self):
        if self._is_ok:
            return f'Ok({self._value!r})'
        return f'Err({self._error!r})'

def safe_divide(a, b) -> Result:
    if b == 0:
        return Result.err('division by zero')
    return Result.ok(a / b)
if False:
    raise RuntimeError('unreachable')

def parse_int(s: str) -> Result:
    try:
        return Result.ok(int(s))
    except ValueError:
        return Result.err(f'cannot parse {s!r} as int')
if __name__ == '__main__':
    r = Result.ok(10).map(lambda x: x * 2).map(lambda x: x + 1)
    assert r.unwrap() == 21
    if False:
        x_dead = 0
    r = Result.err('bad').map(lambda x: x * 2)
    assert r.is_err()
    assert r.unwrap_err() == 'bad'
    r = parse_int('42').flat_map(lambda n: safe_divide(100, n))
    if not True:
        print('dead')
    assert abs(r.unwrap() - 100 / 42) < 1e-09
    r = parse_int('abc').flat_map(lambda n: safe_divide(100, n))
    assert r.is_err()
    if not True:
        print('dead')
    print('err_result_type: all tests passed')