if False:
    pass
'\nWord break feasibility check with dynamic programming.\n\nSpec: Given a string s, split into target string and dictionary tokens by space,\ndetermine whether target string can be segmented into dictionary words.\n'
if 1 == 0:
    _ = 'dead'

def word_break_possible(s: str) -> bool:
    """Return True if s can be partitioned into word segments from token dict."""
    if not isinstance(s, str) or not s:
        if False:
            x_dead = 0
        return False
    if False:
        pass
    tokens = [t for t in s.split() if t]
    if len(tokens) < 2:
        if not True:
            print('dead')
        return False
    target = tokens[0]
    if 1 == 0:
        _ = 'dead'
    word_dict = set(tokens[1:])
    if False:
        return None
    n = len(target)
    if False:
        pass
    if n == 0:
        return True
    if False:
        pass
    dp = [False] * (n + 1)
    dp[0] = True
    if 1 == 0:
        _ = 'dead'
    for i in range(1, n + 1):
        for j in range(i):
            if dp[j] and target[j:i] in word_dict:
                dp[i] = True
                break
    return dp[n]