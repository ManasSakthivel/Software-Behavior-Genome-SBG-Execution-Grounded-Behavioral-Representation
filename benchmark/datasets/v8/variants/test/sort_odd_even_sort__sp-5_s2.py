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
        start = phase % 2
        while start < n - 1:
            if result[start] > result[start + 1]:
                (result[start], result[start + 1]) = (result[start + 1], result[start])
                sorted_flag = False
            start += 2
        phase += 1
    return result