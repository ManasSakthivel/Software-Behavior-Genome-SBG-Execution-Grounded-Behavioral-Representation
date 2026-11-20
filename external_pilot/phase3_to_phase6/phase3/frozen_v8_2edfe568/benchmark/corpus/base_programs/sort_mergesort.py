# program_id: sort_mergesort
# category: sorting_searching
# spec_version: 1.0

"""
Mergesort: stable, out-of-place top-down recursive sort.

Spec: Given a list of comparable elements, return a new sorted list in
ascending order using the mergesort algorithm. The original list is not
mutated. Stable: equal elements preserve their original relative order.
Time complexity O(n log n), space O(n).
"""


def mergesort(arr: list) -> list:
    """Return a new sorted list using top-down mergesort."""
    if len(arr) <= 1:
        return list(arr)

    mid = len(arr) // 2
    left = mergesort(arr[:mid])
    right = mergesort(arr[mid:])
    return _merge(left, right)


def _merge(left: list, right: list) -> list:
    result = []
    i = j = 0
    while i < len(left) and j < len(right):
        # Stable: prefer left on tie
        if left[i] <= right[j]:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
    result.extend(left[i:])
    result.extend(right[j:])
    return result


# ---------- tests ----------

def test_mergesort():
    # Test 1: general unsorted
    assert mergesort([5, 2, 4, 6, 1, 3]) == [1, 2, 3, 4, 5, 6]

    # Test 2: already sorted
    assert mergesort([1, 2, 3]) == [1, 2, 3]

    # Test 3: reverse
    assert mergesort([4, 3, 2, 1]) == [1, 2, 3, 4]

    # Test 4: empty
    assert mergesort([]) == []

    # Test 5: single element
    assert mergesort([99]) == [99]

    # Test 6: duplicates — stability check using tuples
    data = [(1, 'b'), (1, 'a'), (2, 'c')]
    # Sort only by first element; stable sort keeps (1,'b') before (1,'a')
    result = mergesort(data)
    assert result == [(1, 'b'), (1, 'a'), (2, 'c')], f"got {result}"

    # Test 7: large random-ish input
    import random
    rng = random.Random(42)
    big = [rng.randint(0, 1000) for _ in range(500)]
    assert mergesort(big) == sorted(big)

    # Test 8: does not mutate original
    original = [3, 1, 2]
    _ = mergesort(original)
    assert original == [3, 1, 2]

    print("All mergesort tests passed.")


if __name__ == "__main__":
    test_mergesort()
    demo = [38, 27, 43, 3, 9, 82, 10]
    print(f"mergesort({demo}) = {mergesort(demo)}")
