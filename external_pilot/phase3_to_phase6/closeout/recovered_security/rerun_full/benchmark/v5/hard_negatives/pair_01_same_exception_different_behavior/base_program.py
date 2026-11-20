"""
Pair 01 BASE: raises ValueError on negative input, returns x*2 on positive.
"""


def compute(x):
    if x < 0:
        raise ValueError(f"Input must be non-negative, got {x}")
    return x * 2


def run(inputs):
    results = []
    for x in inputs:
        try:
            results.append(compute(x))
        except ValueError as e:
            results.append(f"ValueError: {e}")
    return results
