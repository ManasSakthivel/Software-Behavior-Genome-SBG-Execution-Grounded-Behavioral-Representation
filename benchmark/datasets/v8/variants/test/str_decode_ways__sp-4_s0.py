def decode_ways(s: str) -> int:
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
    for i in range(2, n + 1):
        one_digit = int(s[i - 1])
        two_digits = int(s[i - 2:i])
        if one_digit >= 1:
            dp[i] += dp[i - 1]
        if 10 <= two_digits <= 26:
            dp[i] += dp[i - 2]
    return dp[n]