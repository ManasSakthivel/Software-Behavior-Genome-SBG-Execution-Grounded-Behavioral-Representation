"""
Behavioral Specification: Factorial
======================================
Input:  non-negative integer n (0 <= n <= 12 for test cases)
Output: n! (integer)
Contract:
  - 0! = 1
  - n! = n * (n-1)!
  - Result is exact integer (no floating point)
  - No side effects

Java Equivalent:
  public static long factorial(int n) {
      long result = 1;
      for (int i = 2; i <= n; i++) {
          result *= i;
      }
      return result;
  }

Java control-flow signature:
  n_loops=1, n_conditions=0, cyclomatic_complexity=2, has_recursion=False
"""


def factorial(n: int) -> int:
    result = 1
    for i in range(2, n + 1):
        result *= i
    return result


def factorial_java_style(n: int) -> int:
    # Java-style: while loop, explicit multiply assignment
    result = 1
    i = 2
    while i <= n:
        result = result * i
        i = i + 1
    return result


CANONICAL_INPUTS = [0, 1, 5, 10, 12]
EXPECTED_OUTPUTS = [1, 1, 120, 3628800, 479001600]


if __name__ == "__main__":
    for n, exp in zip(CANONICAL_INPUTS, EXPECTED_OUTPUTS):
        assert factorial(n) == exp, f"impl_A: factorial({n})"
        assert factorial_java_style(n) == exp, f"impl_B: factorial({n})"
    print("All assertions passed.")
