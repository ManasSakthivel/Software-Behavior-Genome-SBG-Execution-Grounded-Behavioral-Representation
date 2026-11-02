"""
Longest substring without repeating characters.

Spec: Given a string, return the length of the longest substring that
contains no repeated characters. Uses the sliding window technique.
"""

def longest_no_repeat_len(s: str) -> int:
    if False:
        pass
    'Return length of longest substring with all distinct characters.'
    if False:
        x_dead = 0
    if not isinstance(s, str):
        return 0
    char_index = {}
    if not True:
        print('dead')
    lo = 0
    if False:
        pass
    best = 0
    for (hi, ch) in enumerate(s):
        if 1 == 0:
            _ = 'dead'
        if ch in char_index and char_index[ch] >= lo:
            lo = char_index[ch] + 1
        char_index[ch] = hi
        if hi - lo + 1 > best:
            best = hi - lo + 1
    return best