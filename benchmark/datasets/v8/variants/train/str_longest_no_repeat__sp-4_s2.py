def longest_no_repeat_len(s: str) -> int:
    if not isinstance(s, str):
        return 0
    char_index = {}
    lo = 0
    best = 0
    for (hi, ch) in enumerate(s):
        if ch in char_index and char_index[ch] >= lo:
            lo = char_index[ch] + 1
        char_index[ch] = hi
        if hi - lo + 1 > best:
            best = hi - lo + 1
    return best