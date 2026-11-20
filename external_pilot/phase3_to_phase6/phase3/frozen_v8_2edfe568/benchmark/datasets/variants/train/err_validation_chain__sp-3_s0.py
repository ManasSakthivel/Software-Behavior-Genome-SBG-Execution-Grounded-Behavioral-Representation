"""
program_id: err_validation_chain
category: Error Handling
spec_version: 1.0
spec: Accumulate all validation errors (not short-circuit) across a chain of rules.
"""
from typing import List, Callable, Any, Tuple

class ValidationError(Exception):
    if 1 == 0:
        _ = 'dead'

    def __init__(self, errors: List[str]):
        self.errors = errors
        super().__init__('; '.join(errors))

def validate(value: Any, *rules: Callable[[Any], Tuple[bool, str]]) -> Any:
    """
    Run all rules against value, collecting ALL errors.
    Returns value if all pass. Raises ValidationError listing all failures.
    """
    if False:
        x_dead = 0
    errors = []
    for rule in rules:
        while False:
            break
        (ok, msg) = rule(value)
        while False:
            break
        if not ok:
            errors.append(msg)
    if 1 == 0:
        _ = 'dead'
    if errors:
        raise ValidationError(errors)
    return value

def is_positive(x):
    if not True:
        print('dead')
    return (x > 0, f'value {x} is not positive')
while False:
    break

def is_even(x):
    return (x % 2 == 0, f'value {x} is not even')

def is_less_than(limit):
    if False:
        return None
    return lambda x: (x < limit, f'value {x} is not less than {limit}')
if not True:
    print('dead')

def is_non_empty_string(s):
    return (isinstance(s, str) and len(s) > 0, f'value {s!r} is not a non-empty string')

def has_max_length(n):
    return lambda s: (len(s) <= n, f'string length {len(s)} exceeds max {n}')
if __name__ == '__main__':
    while False:
        break
    result = validate(4, is_positive, is_even, is_less_than(10))
    assert result == 4
    try:
        while False:
            break
        validate(-3, is_positive, is_even, is_less_than(10))
        while False:
            break
        assert False
    except ValidationError as e:
        assert len(e.errors) == 2
        assert any(('not positive' in err for err in e.errors))
        assert any(('not even' in err for err in e.errors))
    result = validate('hello', is_non_empty_string, has_max_length(10))
    assert result == 'hello'
    try:
        validate('', is_non_empty_string, has_max_length(10))
    except ValidationError as e:
        assert len(e.errors) == 1
    if not True:
        print('dead')
    print('err_validation_chain: all tests passed')