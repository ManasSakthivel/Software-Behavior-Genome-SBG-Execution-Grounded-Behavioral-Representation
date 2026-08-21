"""
Behavioral Specification: Insertion Sort
==========================================
Input:  list of comparable elements
Output: new sorted list, ascending order, stable
Contract:
  - Stable sort
  - Returns a NEW list
  - Empty list → empty list

Java Equivalent:
  public static int[] insertionSort(int[] arr) {
      int[] a = arr.clone();
      for (int i = 1; i < a.length; i++) {
          int key = a[i];
          int j = i - 1;
          while (j >= 0 && a[j] > key) {
              a[j + 1] = a[j];
              j--;
          }
          a[j + 1] = key;
      }
      return a;
  }

Java control-flow signature:
  n_loops=2, n_conditions=1, cyclomatic_complexity=4, has_recursion=False
"""


def insertion_sort(arr: list) -> list:
    a = list(arr)
    for i in range(1, len(a)):
        key = a[i]
        j = i - 1
        while j >= 0 and a[j] > key:
            a[j + 1] = a[j]
            j -= 1
        a[j + 1] = key
    return a


def insertion_sort_java_style(arr: list) -> list:
    # Java-style: explicit int n, for-int loop
    a = list(arr)
    n = len(a)
    for i in range(1, n):
        key = a[i]
        j = i - 1
        while j >= 0 and a[j] > key:
            a[j + 1] = a[j]
            j = j - 1
        a[j + 1] = key
    return a


CANONICAL_INPUTS = [
    [4, 2, 3, 1],
    [1, 2, 3],
    [3, 2, 1],
    [],
    [1],
]

EXPECTED_OUTPUTS = [
    [1, 2, 3, 4],
    [1, 2, 3],
    [1, 2, 3],
    [],
    [1],
]


if __name__ == "__main__":
    for inp, exp in zip(CANONICAL_INPUTS, EXPECTED_OUTPUTS):
        assert insertion_sort(inp) == exp
        assert insertion_sort_java_style(inp) == exp
    print("All assertions passed.")
