"""
Pair 02 VARIANT: Iterates N times, returns product of 1..N (factorial). CHANGED.
Same loop count as base, different computation per iteration.
"""


def compute(n):
    total = 1
    for i in range(1, n + 1):
        total *= i  # CHANGED: += → *=
    return total


def run(inputs):
    return [compute(n) for n in inputs]
