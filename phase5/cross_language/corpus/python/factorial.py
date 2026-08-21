def factorial(n):
    """Return n! for n >= 0. Returns 1 for n=0."""
    if n < 0:
        raise ValueError("n must be non-negative")
    result = 1
    for i in range(2, n + 1):
        result *= i
    return result
