"""
Pair 04 BASE: Computes the sum of a list.
Function named compute_sum, parameter named items.
"""


def compute_sum(items):
    total = 0
    for item in items:
        total += item
    return total


def run(inputs):
    return [compute_sum(lst) for lst in inputs]
