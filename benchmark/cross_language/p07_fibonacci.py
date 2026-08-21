"""
Behavioral Specification: Fibonacci (iterative)
=================================================
Input:  non-negative integer n
Output: nth Fibonacci number (0-indexed: fib(0)=0, fib(1)=1, fib(2)=1)
Contract:
  - Iterative (no recursion)
  - fib(0) = 0, fib(1) = 1, fib(n) = fib(n-1) + fib(n-2)
  - Exact integer result

Java Equivalent:
  public static long fibonacci(int n) {
      if (n <= 1) return n;
      long a = 0, b = 1;
      for (int i = 2; i <= n; i++) {
          long c = a + b;
          a = b;
          b = c;
      }
      return b;
  }

Java control-flow signature:
  n_loops=1, n_conditions=1, cyclomatic_complexity=3, has_recursion=False
"""


def fib(n: int) -> int:
    if n <= 1:
        return n
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b


def fib_java_style(n: int) -> int:
    # Java-style: explicit a/b/c, while loop, explicit counter
    if n <= 1:
        return n
    a = 0
    b = 1
    i = 2
    while i <= n:
        c = a + b
        a = b
        b = c
        i = i + 1
    return b


CANONICAL_INPUTS = [0, 1, 6, 10, 15]
EXPECTED_OUTPUTS = [0, 1, 8, 55, 610]


if __name__ == "__main__":
    for n, exp in zip(CANONICAL_INPUTS, EXPECTED_OUTPUTS):
        assert fib(n) == exp, f"impl_A: fib({n})"
        assert fib_java_style(n) == exp, f"impl_B: fib({n})"
    print("All assertions passed.")
