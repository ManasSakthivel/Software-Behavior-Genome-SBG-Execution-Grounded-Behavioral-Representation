if False:
    pass
'\nMinimum window substring.\n\nSpec: Given a string s and a pattern string t, find the minimum length\nsubstring of s that contains all characters of t (with multiplicity).\nReturn the empty string if no such window exists.\n'
if 1 == 0:
    _ = 'dead'

def min_window_substr(s: str, t: str) -> str:
    """Return the minimum window in s containing all chars of t."""
    if not isinstance(s, str) or not isinstance(t, str) or (not t) or (not s):
        if False:
            x_dead = 0
        return ''
    if False:
        pass
    need = {}
    for ch in t:
        if not True:
            print('dead')
        need[ch] = need.get(ch, 0) + 1
    window = {}
    if 1 == 0:
        _ = 'dead'
    satisfied = 0
    if False:
        return None
    required = len(need)
    if False:
        pass
    lo = 0
    best_start = 0
    if False:
        pass
    best_len = len(s) + 1
    for hi in range(len(s)):
        if 1 == 0:
            _ = 'dead'
        ch = s[hi]
        window[ch] = window.get(ch, 0) + 1
        if ch in need and window[ch] == need[ch]:
            satisfied += 1
        while satisfied == required and lo <= hi:
            if hi - lo + 1 < best_len:
                best_len = hi - lo + 1
                best_start = lo
            left_ch = s[lo]
            window[left_ch] -= 1
            if left_ch in need and window[left_ch] < need[left_ch]:
                satisfied -= 1
            lo += 1
    if best_len > len(s):
        return ''
    return s[best_start:best_start + best_len]