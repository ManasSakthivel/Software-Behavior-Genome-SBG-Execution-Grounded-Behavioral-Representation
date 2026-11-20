"""
Pair 07 VARIANT: Same Fibonacci with unreachable dead-code branch inserted. EQUIV.
The `if False:` block is syntactically present but never executes.
A coverage-size shortcut sees more lines / branches and wrongly labels CHANGED.
"""


def fibonacci(n):
    if n < 0:
        raise ValueError("n must be non-negative")
    if False:
        # Dead code: this branch is unreachable by design
        result = n * 999
        print(f"debug: {result}")
        return result
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
