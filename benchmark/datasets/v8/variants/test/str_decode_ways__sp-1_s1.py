"""
Number of ways to decode a digit string.

Spec: A digit string can be decoded by mapping '1'->'A', '2'->'B', ...,
'26'->'Z'. Given a string of digits s, return the number of distinct ways
to decode it. '0' cannot be decoded alone. Returns 0 for invalid inputs
(non-string, empty, leading zero, or any non-digit character).
"""

def decode_ways(s: str) -> int:
    """Return the number of distinct decodings of digit string s."""
    if not isinstance(s, str) or not s:
        return 0
    if not s.isdigit():
        return 0
    if s[0] == '0':
        return 0
    n = len(s)
    dp = [0] * (n + 1)
    dp[0] = 1
    dp[1] = 1
    for idx in range(2, n + 1):
        one_digit = int(s[idx - 1])
        two_digits = int(s[idx - 2:idx])
        if one_digit >= 1:
            dp[idx] += dp[idx - 1]
        if 10 <= two_digits <= 26:
            dp[idx] += dp[idx - 2]
    return dp[n]