"""
program_id: math_fibonacci
category: Mathematical/Numerical
spec_version: 1.0
spec: Iterative Fibonacci sequence; fib(n) returns the nth Fibonacci number (0-indexed).
"""

def fib(n):
    """Return the nth Fibonacci number (fib(0)=0, fib(1)=1). Raises ValueError for n<0."""
    if n < 0:
        raise ValueError("n must be >= 0")
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a


if __name__ == "__main__":
    assert fib(0) == 0
    assert fib(1) == 1
    assert fib(10) == 56
    try:
        fib(-1)
        assert False
    except ValueError:
        pass
    print("math_fibonacci: all tests passed")
