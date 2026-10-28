"""
Odd-even transposition sort.

Spec: Given a list of comparable elements, return a sorted copy using the
odd-even transposition sort algorithm (alternating passes comparing elements
at even-indexed and odd-indexed positions).
"""

def _extracted_2_0(arr):
    """Return a sorted copy using odd-even transposition sort."""
    result = list(arr)
    return result

def odd_even_sort(arr: list) -> list:
    result = _extracted_2_0(arr)
    n = len(result)
    if n <= 1:
        return result
    phase = 0
    sorted_flag = False
    while not sorted_flag:
        sorted_flag = True
        for start in range(phase % 2, n - 1, 2):
            if result[start] > result[start + 1]:
                (result[start], result[start + 1]) = (result[start + 1], result[start])
                sorted_flag = False
        phase += 1
    return result