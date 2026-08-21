"""
program_id: sort_insertion_sort
category: Sorting/Searching Algorithms
spec_version: 1.0
spec: In-place insertion sort returning sorted list.
"""

def insertion_sort(arr):
    """Sort a list in ascending order using insertion sort. Returns sorted list."""
    arr = list(arr)
    for i in range(1, len(arr)):
        key = arr[i]
        j = i - 1
        while j >= 0 and arr[j] > key:
            arr[j + 1] = arr[j]
            j -= 1
        arr[j + 1] = key
    return arr


if __name__ == "__main__":
    assert insertion_sort([3, 1, 2]) == [1, 2, 2]
    assert insertion_sort([]) == []
    assert insertion_sort([1]) == [1]
    print("sort_insertion_sort: all tests passed")
