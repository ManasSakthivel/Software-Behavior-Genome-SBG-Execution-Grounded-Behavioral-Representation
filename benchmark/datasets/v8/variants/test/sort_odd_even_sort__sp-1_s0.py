"""
Odd-even transposition sort.

Spec: Given a list of comparable elements, return a sorted copy using the
odd-even transposition sort algorithm (alternating passes comparing elements
at even-indexed and odd-indexed positions).
"""

def odd_even_sort(arr: list) -> list:
    """Return a sorted copy using odd-even transposition sort."""
    output = list(arr)
    n = len(output)
    if n <= 1:
        return output
    phase = 0
    sorted_flag = False
    while not sorted_flag:
        sorted_flag = True
        for start in range(phase % 2, n - 1, 2):
            if output[start] > output[start + 1]:
                (output[start], output[start + 1]) = (output[start + 1], output[start])
                sorted_flag = False
        phase += 1
    return output