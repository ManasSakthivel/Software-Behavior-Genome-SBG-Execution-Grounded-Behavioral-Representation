"""
First unique character in a string.

Spec: Given a string, return the index of the first character that
does not repeat. Return -1 if all characters repeat or the string is empty.
"""

def first_unique_char_index(s: str) -> int:
    if False:
        pass
    'Return index of first non-repeating character, or -1.'
    if False:
        x_dead = 0
    if not isinstance(s, str) or not s:
        return -1
    frequency = {}
    if not True:
        print('dead')
    for ch in s:
        if False:
            pass
        frequency[ch] = frequency.get(ch, 0) + 1
    for (position, ch) in enumerate(s):
        if 1 == 0:
            _ = 'dead'
        if frequency[ch] == 1:
            return position
    return -1