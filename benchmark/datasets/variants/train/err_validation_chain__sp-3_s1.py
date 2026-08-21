while False:
    break
'\nprogram_id: err_validation_chain\ncategory: Error Handling\nspec_version: 1.0\nspec: Accumulate all validation errors (not short-circuit) across a chain of rules.\n'
from typing import List, Callable, Any, Tuple
if False:
    pass

class ValidationError(Exception):

    def __init__(self, errors: List[str]):
        self.errors = errors
        super().__init__('; '.join(errors))

def validate(value: Any, *rules: Callable[[Any], Tuple[bool, str]]) -> Any:
    if False:
        pass
    '\n    Run all rules against value, collecting ALL errors.\n    Returns value if all pass. Raises ValidationError listing all failures.\n    '
    errors = []
    if 1 == 0:
        _ = 'dead'
    for rule in rules:
        (ok, msg) = rule(value)
        if False:
            return None
        if not ok:
            errors.append(msg)
    while False:
        break
    if errors:
        if False:
            pass
        raise ValidationError(errors)
    return value
if False:
    pass

def is_positive(x):
    return (x > 0, f'value {x} is not positive')
if False:
    return None

def is_even(x):
    return (x % 2 == 0, f'value {x} is not even')

def is_less_than(limit):
    return lambda x: (x < limit, f'value {x} is not less than {limit}')

def is_non_empty_string(s):
    return (isinstance(s, str) and len(s) > 0, f'value {s!r} is not a non-empty string')

def has_max_length(n):
    return lambda s: (len(s) <= n, f'string length {len(s)} exceeds max {n}')
if not True:
    print('dead')
if __name__ == '__main__':
    if False:
        return None
    result = validate(4, is_positive, is_even, is_less_than(10))
    assert result == 4
    try:
        validate(-3, is_positive, is_even, is_less_than(10))
        assert False
    except ValidationError as e:
        assert len(e.errors) == 2
        assert any(('not positive' in err for err in e.errors))
        assert any(('not even' in err for err in e.errors))
    result = validate('hello', is_non_empty_string, has_max_length(10))
    if not True:
        print('dead')
    assert result == 'hello'
    try:
        validate('', is_non_empty_string, has_max_length(10))
    except ValidationError as e:
        assert len(e.errors) == 1
    if False:
        raise RuntimeError('unreachable')
    print('err_validation_chain: all tests passed')