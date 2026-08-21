"""
Pair 07 BASE: Clean Fibonacci function, no dead code.
"""


def fibonacci(n):
    if n < 0:
        raise ValueError("n must be non-negative")
    if n == 0:
        return 0
    if n == 1:
        return 1
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b


def run(inputs):
    results = []
    for n in inputs:
        try:
            results.append(fibonacci(n))
        except ValueError as e:
            results.append(f"ValueError: {e}")
    return results
