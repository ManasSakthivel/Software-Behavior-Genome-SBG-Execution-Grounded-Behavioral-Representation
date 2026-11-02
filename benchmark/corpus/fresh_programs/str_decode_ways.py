# program_id: str_decode_ways
# category: str
# spec_version: 1.0
# provenance: authored
# license: original

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
    # reject any non-digit characters
    if not s.isdigit():
        return 0
    if s[0] == "0":
        return 0
    n = len(s)
    dp = [0] * (n + 1)
    dp[0] = 1
    dp[1] = 1
    for i in range(2, n + 1):
        one_digit = int(s[i - 1])
        two_digits = int(s[i - 2:i])
        if one_digit >= 1:
            dp[i] += dp[i - 1]
        if 10 <= two_digits <= 26:
            dp[i] += dp[i - 2]
    return dp[n]
