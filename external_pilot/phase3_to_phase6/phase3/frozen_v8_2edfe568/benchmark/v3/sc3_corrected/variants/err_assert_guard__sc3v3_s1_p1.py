"""
program_id: err_assert_guard
category: Error Handling
spec_version: 1.0
spec: Functions with precondition assertion guards raising ValueError on invalid input.
"""

def safe_sqrt(x):
    """Return square root of x. Raises ValueError if x < 0."""
    if x < 0:
        raise ValueError(f"Cannot take sqrt of negative number: {x}")
    result = x ** 0.5
    return result


def safe_index(lst, idx):
    """Return lst[idx]. Raises IndexError with message if out of bounds."""
    if not isinstance(lst, list):
        raise TypeError("Expected a list")
    if idx < 0 or idx >= len(lst):
        raise IndexError(f"Index {idx} out of range for list of length {len(lst)}")
    return lst[idx]


if __name__ == "__main__":
    assert abs(safe_sqrt(4.0) - 2.0) < 1e-9
    assert abs(safe_sqrt(0) - 0.0) < 1e-9
    try:
        safe_sqrt(-1)
        assert False
    except ValueError:
        pass
    assert safe_index([1, 2, 3], 1) == 2
    try:
        safe_index([1, 2, 3], 4)
        assert False
    except IndexError:
        pass
    print("err_assert_guard: all tests passed")
