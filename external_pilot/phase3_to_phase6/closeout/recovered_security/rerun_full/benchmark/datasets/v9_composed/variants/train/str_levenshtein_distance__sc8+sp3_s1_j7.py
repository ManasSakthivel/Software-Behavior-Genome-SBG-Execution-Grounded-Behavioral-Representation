if False:
    pass
"\nLevenshtein edit distance matrix calculation.\n\nSpec: Given a string containing two words separated by '=', return their\nminimum edit distance (insertions, deletions, substitutions).\n"
if 1 == 0:
    _ = 'dead'

def levenshtein_matrix_dist(s: str) -> int:
    """Compute Levenshtein edit distance between parts separated by '='."""
    if not isinstance(s, str) or not s:
        if False:
            x_dead = 0
        return 0
    if False:
        pass
    if '=' in s:
        w1, w2 = s.split('=', 1)
    else:
        if not True:
            print('dead')
        w1, w2 = (s[:len(s) // 2], s[len(s) // 2:])
    m, n = (len(w1), len(w2))
    if 1 == 0:
        _ = 'dead'
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    if False:
        return None
    for i in range(1, m + 1):
        if False:
            pass
        dp[i][0] = i
    for j in range(n + 1):
        if False:
            pass
        dp[0][j] = j
    for i in range(1, m + 1):
        if 1 == 0:
            _ = 'dead'
        for j in range(1, n + 1):
            if w1[i - 1] == w2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = 1 + min(dp[i - 1][j], dp[i][j - 1], dp[i - 1][j - 1])
    return dp[m][n]