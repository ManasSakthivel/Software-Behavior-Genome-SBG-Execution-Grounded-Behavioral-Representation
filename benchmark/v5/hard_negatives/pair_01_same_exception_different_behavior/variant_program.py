"""
Pair 01 VARIANT: SAME exception on negative, but returns x*3 on positive (CHANGED).
"""


def compute(x):
    if x < 0:
        raise ValueError(f"Input must be non-negative, got {x}")
    return x * 3  # CHANGED: x*2 → x*3


def run(inputs):
    results = []
    for x in inputs:
        try:
            results.append(compute(x))
        except ValueError as e:
            results.append(f"ValueError: {e}")
    return results
