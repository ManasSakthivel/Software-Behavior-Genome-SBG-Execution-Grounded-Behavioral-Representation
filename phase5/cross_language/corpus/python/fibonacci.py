def fibonacci(n):
    """Return nth Fibonacci number (0-indexed). fib(0)=0, fib(1)=1."""
    if n < 0:
        raise ValueError("n must be non-negative")
    if n == 0:
        return 0
    a, b = 0, 1
    for _ in range(1, n):
        a, b = b, a + b
    return b
