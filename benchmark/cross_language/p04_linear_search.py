"""
Behavioral Specification: Linear Search
=========================================
Input:  list of elements, target element
Output: index of first occurrence of target, or -1 if absent
Contract:
  - Returns the index of the FIRST occurrence
  - Returns -1 if not found
  - Works on any list (unsorted)
  - Empty list → -1

Java Equivalent:
  public static int linearSearch(int[] arr, int target) {
      for (int i = 0; i < arr.length; i++) {
          if (arr[i] == target) return i;
      }
      return -1;
  }

Java control-flow signature:
  n_loops=1, n_conditions=1, cyclomatic_complexity=3, has_recursion=False
"""


def linear_search(arr: list, target) -> int:
    for i, v in enumerate(arr):
        if v == target:
            return i
    return -1


def linear_search_java_style(arr: list, target) -> int:
    # Java-style: explicit index counter
    i = 0
    while i < len(arr):
        if arr[i] == target:
            return i
        i += 1
    return -1


CANONICAL_INPUTS = [
    ([1, 2, 3, 4], 3),
    ([1, 2, 3], 5),
    ([], 1),
    ([7, 7, 7], 7),
    ([10, 20, 30, 10], 10),
]

EXPECTED_OUTPUTS = [2, -1, -1, 0, 0]


if __name__ == "__main__":
    for (arr, target), exp in zip(CANONICAL_INPUTS, EXPECTED_OUTPUTS):
        assert linear_search(arr, target) == exp
        assert linear_search_java_style(arr, target) == exp
    print("All assertions passed.")
