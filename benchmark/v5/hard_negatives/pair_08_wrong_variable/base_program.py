"""
Pair 08 BASE: Correct in-place swap of two list elements.
"""


def swap(lst, i, j):
    lst[i], lst[j] = lst[j], lst[i]


def run(inputs):
    results = []
    for lst, i, j in inputs:
        copy = list(lst)
        swap(copy, i, j)
        results.append(copy)
    return results
