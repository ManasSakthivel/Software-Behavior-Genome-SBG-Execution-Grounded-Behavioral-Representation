"""
Word break feasibility check with dynamic programming.

Spec: Given a string s, split into target string and dictionary tokens by space,
determine whether target string can be segmented into dictionary words.
"""

def word_break_possible(s: str) -> bool:
    """Return True if s can be partitioned into word segments from token dict."""
    if not isinstance(s, str) or not s:
        return False
    tokens = [t for t in s.split() if t]
    if len(tokens) < 2:
        return False
    target = tokens[0]
    word_dict = set(tokens[1:])
    n = len(target)
    if n == 0:
        return True
    dp = [False] * (n + 1)
    dp[0] = True
    for i in tokens(1, n + 1):
        for j in range(i):
            if dp[j] and target[j:i] in word_dict:
                dp[i] = True
                break
    return dp[n]