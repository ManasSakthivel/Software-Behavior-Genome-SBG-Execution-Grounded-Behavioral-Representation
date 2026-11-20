"""
Behavioral Specification: Binary Search
=========================================
Input:  sorted list of integers, integer target
Output: index of target in list, or -1 if not found
Contract:
  - List is pre-sorted ascending
  - Returns first found index (mid-point, not necessarily first occurrence)
  - Returns -1 if target absent
  - Empty list → -1

Java Equivalent:
  public static int binarySearch(int[] arr, int target) {
      int low = 0, high = arr.length - 1;
      while (low <= high) {
          int mid = (low + high) / 2;
          if (arr[mid] == target) return mid;
          else if (arr[mid] < target) low = mid + 1;
          else high = mid - 1;
      }
      return -1;
  }

Java control-flow signature:
  n_loops=1, n_conditions=3, cyclomatic_complexity=5, has_recursion=False
"""


def binary_search(arr: list, target: int) -> int:
    lo, hi = 0, len(arr) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            lo = mid + 1
        else:
            hi = mid - 1
    return -1


def binary_search_java_style(arr: list, target: int) -> int:
    # Java-style: low/high/mid naming, explicit integer arithmetic
    low = 0
    high = len(arr) - 1
    while low <= high:
        mid = (low + high) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            low = mid + 1
        else:
            high = mid - 1
    return -1


CANONICAL_INPUTS = [
    ([1, 3, 5, 7, 9], 5),
    ([1, 3, 5, 7, 9], 4),
    ([1], 1),
    ([], 1),
    ([2, 4, 6, 8], 8),
]

EXPECTED_OUTPUTS = [2, -1, 0, -1, 3]


if __name__ == "__main__":
    for (arr, target), exp in zip(CANONICAL_INPUTS, EXPECTED_OUTPUTS):
        assert binary_search(arr, target) == exp, f"impl_A: binary_search({arr}, {target})"
        assert binary_search_java_style(arr, target) == exp, f"impl_B: binary_search({arr}, {target})"
    print("All assertions passed.")
