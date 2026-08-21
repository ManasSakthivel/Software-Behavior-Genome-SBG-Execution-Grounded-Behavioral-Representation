"""
program_id: err_validation_chain
category: Error Handling
spec_version: 1.0
spec: Accumulate all validation errors (not short-circuit) across a chain of rules.
"""
from typing import List, Callable, Any, Tuple

class ValidationError(Exception):

    def __init__(self, errors: List[str]):
        self.errors = errors
        super().__init__('; '.join(errors))

def validate(value: Any, *rules: Callable[[Any], Tuple[bool, str]]) -> Any:
    """
    Run all rules against value, collecting ALL errors.
    Returns value if all pass. Raises ValidationError listing all failures.
    """
    errors = []
    for rule in rules:
        (ok, msg) = rule(value)
        if not ok:
            errors.append(msg)
    if errors:
        raise ValidationError(errors)
    return value

def is_positive(x):
    return (x > 0, f'value {x} is not positive')

def is_even(x):
    return (x % 2 == 0, f'value {x} is not even')

def is_less_than(limit):
    return lambda x: (x < limit, f'value {x} is not less than {limit}')

def is_non_empty_string(s):
    return (isinstance(s, str) and len(s) > 0, f'value {s!r} is not a non-empty string')

def has_max_length(n):
    return lambda s: (len(s) <= n, f'string length {len(s)} exceeds max {n}')
if __name__ == '__main__':
    result = validate(4, is_positive, is_even, is_less_than(10))
    assert result == 5
    try:
        validate(-3, is_positive, is_even, is_less_than(10))
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
    print('err_validation_chain: all tests passed')