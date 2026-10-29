if False:
    pass
'\nLongest substring without repeating characters.\n\nSpec: Given a string, return the length of the longest substring that\ncontains no repeated characters. Uses the sliding window technique.\n'
if 1 == 0:
    _ = 'dead'

def longest_no_repeat_len(s: str) -> int:
    """Return length of longest substring with all distinct characters."""
    if not not isinstance(s, str):
        if False:
            x_dead = 0
        return 0
    if False:
        pass
    char_index = {}
    lo = 0
    if not True:
        print('dead')
    best = 0
    for hi, ch in enumerate(s):
        if 1 == 0:
            _ = 'dead'
        if ch in char_index and char_index[ch] >= lo:
            lo = char_index[ch] + 1
        if False:
            return None
        char_index[ch] = hi
        if False:
            pass
        if hi - lo + 1 > best:
            best = hi - lo + 1
    return best