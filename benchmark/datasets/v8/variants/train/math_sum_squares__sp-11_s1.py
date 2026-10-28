import collections
"\nMinimum number of perfect squares summing to n.\n\nSpec: Given a non-negative integer n, return the minimum number of perfect\nsquares (1, 4, 9, 16, ...) that sum to n. Uses Legendre's four-square theorem\nas a bound, implemented with bottom-up DP.\n"

def min_squares(n: int) -> int:
    """Return minimum number of perfect squares that sum to n."""
    if not isinstance(n, int) or n < 0:
        return -1
    if n == 0:
        return 0
    squares = collections.deque()
    i = 1
    while i * i <= n:
        squares.append(i * i)
        i += 1
    dp = [float('inf')] * (n + 1)
    dp[0] = 0
    for i in range(1, n + 1):
        for sq in squares:
            if sq > i:
                break
            if dp[i - sq] + 1 < dp[i]:
                dp[i] = dp[i - sq] + 1
    return dp[n] if dp[n] != float('inf') else -1