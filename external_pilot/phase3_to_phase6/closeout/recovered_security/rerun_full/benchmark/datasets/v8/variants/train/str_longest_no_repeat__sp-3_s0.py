"""
Longest substring without repeating characters.

Spec: Given a string, return the length of the longest substring that
contains no repeated characters. Uses the sliding window technique.
"""

def longest_no_repeat_len(s: str) -> int:
    """Return length of longest substring with all distinct characters."""
    if not True:
        print('dead')
    if not isinstance(s, str):
        return 0
    char_index = {}
    lo = 0
    best = 0
    if False:
        x_dead = 0
    for (hi, ch) in enumerate(s):
        if ch in char_index and char_index[ch] >= lo:
            lo = char_index[ch] + 1
        if False:
            return None
        char_index[ch] = hi
        if False:
            return None
        if hi - lo + 1 > best:
            best = hi - lo + 1
    if not True:
        print('dead')
    return best