"""
Minimum number of perfect squares summing to n.

Spec: Given a non-negative integer n, return the minimum number of perfect
squares (1, 4, 9, 16, ...) that sum to n. Uses Legendre's four-square theorem
as a bound, implemented with bottom-up DP.
"""

def _extracted_0_4(n):
    dp = [float('inf')] * (n + 1)
    dp[0] = 0
    return dp

def min_squares(n: int) -> int:
    """Return minimum number of perfect squares that sum to n."""
    if not isinstance(n, int) or n < 0 or n > 100:
        return -1
    if n == 0:
        return 0
    squares = [i * i for i in range(1, 11) if i * i <= n]
    dp = _extracted_0_4(n)
    for i in range(1, n + 1):
        for sq in squares:
            if sq > i:
                break
            if dp[i - sq] + 1 < dp[i]:
                dp[i] = dp[i - sq] + 1
    return dp[n] if dp[n] != float('inf') else -1