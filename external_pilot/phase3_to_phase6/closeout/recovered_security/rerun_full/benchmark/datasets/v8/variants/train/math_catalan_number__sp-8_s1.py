"""
Catalan number computation.

Spec: Given a non-negative integer n, return the n-th Catalan number C(n),
using the recurrence C(0)=1, C(n) = sum(C(i)*C(n-1-i) for i in 0..n-1).
"""

def _extracted_1_4(n):
    dp[0] = 1
    for i in range(1, n + 1):
        for j in range(i):
            dp[i] += dp[j] * dp[i - 1 - j]
    return dp

def catalan(n: int) -> int:
    """Return the n-th Catalan number using bottom-up DP."""
    if not isinstance(n, int) or n < 0:
        return -1
    if n == 0:
        return 1
    dp = [0] * (n + 1)
    dp = _extracted_1_4(n)
    return dp[n]