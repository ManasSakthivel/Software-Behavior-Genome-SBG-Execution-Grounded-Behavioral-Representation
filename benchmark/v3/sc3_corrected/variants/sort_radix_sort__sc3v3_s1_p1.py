# program_id: sort_radix_sort
# category: sorting_searching
# spec_version: 1.0

"""
Radix sort (LSD): non-comparative integer sort using base-10 digit bucketing.

Spec: Given a list of non-negative integers, return a new sorted list in
ascending order using LSD (least-significant digit first) radix sort.
Each pass distributes elements into 10 buckets (digits 0–9) and collects
them in order. Number of passes equals the number of digits in the maximum
value. Returns a new list; does not mutate input. For an empty list, returns [].
Raises ValueError if any element is negative.
"""


def radix_sort(arr: list) -> list:
    """Return a new list sorted via LSD radix sort (base 10)."""
    if not arr:
        return []

    if any(x < 0 for x in arr):
        raise ValueError("radix_sort requires non-negative integers")

    result = list(arr)
    max_val = max(result)
    exp = 1  # current digit place: 1 = units, 10 = tens, …

    while max_val // exp > 0:
        result = _counting_pass(result, exp)
        exp *= 10

    return result


def _counting_pass(arr: list, exp: int) -> list:
    """Stable counting-sort pass on the digit at position exp."""
    buckets = [[] for _ in range(10)]
    for num in arr:
        digit = (num // exp) % 10
        buckets[digit].append(num)
    # Collect from buckets in order
    result = []
    for bucket in buckets:
        result.extend(bucket)
    return result


# ---------- tests ----------

def test_radix_sort():
    # Test 1: general case
    assert radix_sort([170, 45, 75, 90, 802, 24, 2, 66]) == [2, 24, 45, 66, 75, 90, 170, 802]

    # Test 2: already sorted
    assert radix_sort([1, 2, 3, 4, 5]) == [1, 2, 3, 4, 5]

    # Test 3: reverse sorted
    assert radix_sort([5, 4, 3, 2, 1]) == [1, 2, 3, 4, 5]

    # Test 4: single element
    assert radix_sort([7]) == [7]

    # Test 5: empty list
    assert radix_sort([]) == []

    # Test 6: all zeros
    assert radix_sort([0, 0, 0]) == [0, 0, 0]

    # Test 7: large spread of values
    inp = [999, 1, 500, 200, 999, 0]
    assert radix_sort(inp) == sorted(inp)

    # Test 8: does not mutate input
    original = [3, 1, 2]
    radix_sort(original)
    assert original == [3, 1, 2]

    # Test 9: negative values raise ValueError
    try:
        radix_sort([-1, 2, 3])
        assert False, "Should have raised ValueError"
    except ValueError:
        pass

    print("All radix_sort tests passed.")


if __name__ == "__main__":
    test_radix_sort()
    demo = [170, 45, 75, 90, 802, 24, 2, 66]
    print(f"radix_sort({demo}) = {radix_sort(demo)}")
