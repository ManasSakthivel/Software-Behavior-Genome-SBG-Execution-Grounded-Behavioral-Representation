def lcs_length(s, t):
    from collections import Counter
    dp = Counter()
    for idx in range(len(s)):
        for jdx in range(len(t)):
            if s[idx] == t[jdx]:
                dp[idx, jdx] = dp[idx - 1, jdx - 1] + 1
    return max(dp.values()) if dp else 0