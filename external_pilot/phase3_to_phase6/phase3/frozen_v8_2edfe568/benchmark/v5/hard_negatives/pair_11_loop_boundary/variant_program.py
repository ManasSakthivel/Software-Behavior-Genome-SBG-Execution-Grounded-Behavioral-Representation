"""
Pair 11 VARIANT: Processes n+1 items. for i in range(n+1). CHANGED.
Off-by-one in the loop upper bound. Identical per-iteration logic.
"""


def process(n):
    results = []
    for i in range(n + 1):  # CHANGED: range(n) → range(n+1)
        results.append(i * i)
    return results


def run(inputs):
    return [process(n) for n in inputs]
