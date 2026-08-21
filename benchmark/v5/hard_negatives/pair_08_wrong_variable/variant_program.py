"""
Pair 08 VARIANT: Swap that assigns each element to itself (no-op). CHANGED.
lst[i], lst[j] = lst[i], lst[j]  — right-hand side evaluates BEFORE assignment,
but both slots receive the original values (identity assignment). No actual swap.
"""


def swap(lst, i, j):
    lst[i], lst[j] = lst[i], lst[j]  # CHANGED: swaps with itself


def run(inputs):
    results = []
    for lst, i, j in inputs:
        copy = list(lst)
        swap(copy, i, j)
        results.append(copy)
    return results
