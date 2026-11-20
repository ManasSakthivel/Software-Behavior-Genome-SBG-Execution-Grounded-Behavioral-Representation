"""
Behavioral Specification: Bubble Sort
======================================
Input:  list of comparable elements (integers in tests)
Output: new sorted list, ascending order
Contract:
  - Preserves all elements (no loss, no duplication)
  - Stable sort (equal elements maintain original relative order)
  - Returns a NEW list (does not mutate input)
  - Empty list → empty list
  - Single element → same single-element list

Java Equivalent:
  public static int[] bubbleSort(int[] arr) {
      int[] a = arr.clone();
      int n = a.length;
      for (int i = 0; i < n - 1; i++) {
          for (int j = 0; j < n - 1 - i; j++) {
              if (a[j] > a[j + 1]) {
                  int temp = a[j];
                  a[j] = a[j + 1];
                  a[j + 1] = temp;
              }
          }
      }
      return a;
  }

Java control-flow signature:
  n_loops=2, n_conditions=1, cyclomatic_complexity=4, has_recursion=False
"""

# Implementation A — Python idiomatic (tuple swap)
def bubble_sort(arr: list) -> list:
    a = list(arr)
    for i in range(len(a) - 1):
        for j in range(len(a) - 1 - i):
            if a[j] > a[j + 1]:
                a[j], a[j + 1] = a[j + 1], a[j]
    return a


# Implementation B — Java-idiomatic style (explicit temp variable, while loops)
def bubble_sort_java_style(arr: list) -> list:
    a = list(arr)
    n = len(a)
    i = 0
    while i < n - 1:
        j = 0
        while j < n - 1 - i:
            if a[j] > a[j + 1]:
                temp = a[j]
                a[j] = a[j + 1]
                a[j + 1] = temp
            j = j + 1
        i = i + 1
    return a


# Canonical test inputs (v2 canonical input registry)
CANONICAL_INPUTS = [
    [5, 3, 1, 4, 2],
    [1],
    [],
    [3, 3, 1],
    [-1, 0, 1],
]

EXPECTED_OUTPUTS = [
    [1, 2, 3, 4, 5],
    [1],
    [],
    [1, 3, 3],
    [-1, 0, 1],
]


if __name__ == "__main__":
    for inp, exp in zip(CANONICAL_INPUTS, EXPECTED_OUTPUTS):
        a = bubble_sort(inp)
        b = bubble_sort_java_style(inp)
        assert a == exp, f"impl_A failed: {inp} → {a} (expected {exp})"
        assert b == exp, f"impl_B failed: {inp} → {b} (expected {exp})"
    print("All assertions passed.")
