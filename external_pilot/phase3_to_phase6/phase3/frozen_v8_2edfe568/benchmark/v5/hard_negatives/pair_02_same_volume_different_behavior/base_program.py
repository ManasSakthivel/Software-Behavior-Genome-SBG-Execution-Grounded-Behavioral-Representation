"""
Pair 02 BASE: Iterates N times, returns sum of 1..N.
"""


def compute(n):
    total = 0
    for i in range(1, n + 1):
        total += i
    return total


def run(inputs):
    return [compute(n) for n in inputs]
