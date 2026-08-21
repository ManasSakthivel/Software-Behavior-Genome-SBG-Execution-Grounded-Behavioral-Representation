"""
Behavioral Specification: Greatest Common Divisor (Euclidean)
==============================================================
Input:  two positive integers a, b
Output: GCD(a, b) as a positive integer
Contract:
  - Euclidean algorithm (iterative)
  - GCD(a, 0) = a; GCD(0, b) = b
  - Result is always positive

Java Equivalent:
  public static int gcd(int a, int b) {
      while (b != 0) {
          int temp = b;
          b = a % b;
          a = temp;
      }
      return a;
  }

Java control-flow signature:
  n_loops=1, n_conditions=0, cyclomatic_complexity=2, has_recursion=False
"""


def gcd(a: int, b: int) -> int:
    while b:
        a, b = b, a % b
    return a


def gcd_java_style(a: int, b: int) -> int:
    # Java-style: explicit temp variable, explicit != 0 condition
    while b != 0:
        temp = b
        b = a % b
        a = temp
    return a


CANONICAL_INPUTS = [(12, 8), (100, 75), (7, 3), (1, 1), (48, 18)]
EXPECTED_OUTPUTS = [4, 25, 1, 1, 6]


if __name__ == "__main__":
    for (a, b), exp in zip(CANONICAL_INPUTS, EXPECTED_OUTPUTS):
        assert gcd(a, b) == exp, f"impl_A: gcd({a}, {b})"
        assert gcd_java_style(a, b) == exp, f"impl_B: gcd({a}, {b})"
    print("All assertions passed.")
