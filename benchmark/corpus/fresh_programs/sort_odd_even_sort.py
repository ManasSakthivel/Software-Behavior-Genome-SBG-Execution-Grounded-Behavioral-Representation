# program_id: sort_odd_even_sort
# category: sort
# spec_version: 1.0
# provenance: authored
# license: original

"""
Odd-even transposition sort.

Spec: Given a list of comparable elements, return a sorted copy using the
odd-even transposition sort algorithm (alternating passes comparing elements
at even-indexed and odd-indexed positions).
"""


def odd_even_sort(arr: list) -> list:
    """Return a sorted copy using odd-even transposition sort."""
    result = list(arr)
    n = len(result)
    if n <= 1:
        return result
    phase = 0
    sorted_flag = False
    while not sorted_flag:
        sorted_flag = True
        # even phase: compare (0,1), (2,3), (4,5), ...
        # odd phase: compare (1,2), (3,4), (5,6), ...
        for start in range(phase % 2, n - 1, 2):
            if result[start] > result[start + 1]:
                result[start], result[start + 1] = result[start + 1], result[start]
                sorted_flag = False
        phase += 1
    return result
