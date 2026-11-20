"""
Behavioral Specification: Sum of List
=======================================
Input:  list of integers
Output: integer sum of all elements
Contract:
  - Empty list → 0
  - Negative numbers supported
  - No overflow handling needed (Python has arbitrary precision)

Java Equivalent:
  public static int sumList(int[] arr) {
      int total = 0;
      for (int i = 0; i < arr.length; i++) {
          total += arr[i];
      }
      return total;
  }

Java control-flow signature:
  n_loops=1, n_conditions=0, cyclomatic_complexity=2, has_recursion=False
"""


def sum_list(arr: list) -> int:
    return sum(arr)


def sum_list_java_style(arr: list) -> int:
    # Java-style: explicit index loop, += notation spelled out
    total = 0
    i = 0
    while i < len(arr):
        total = total + arr[i]
        i = i + 1
    return total


CANONICAL_INPUTS = [
    [1, 2, 3],
    [],
    [5],
    [-1, 1],
    [10, 20, 30],
]
EXPECTED_OUTPUTS = [6, 0, 5, 0, 60]


if __name__ == "__main__":
    for arr, exp in zip(CANONICAL_INPUTS, EXPECTED_OUTPUTS):
        assert sum_list(arr) == exp, f"impl_A: sum_list({arr})"
        assert sum_list_java_style(arr) == exp, f"impl_B: sum_list({arr})"
    print("All assertions passed.")
