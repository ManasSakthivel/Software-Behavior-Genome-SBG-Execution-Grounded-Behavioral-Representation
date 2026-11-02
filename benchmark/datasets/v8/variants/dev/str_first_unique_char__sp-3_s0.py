"""
First unique character in a string.

Spec: Given a string, return the index of the first character that
does not repeat. Return -1 if all characters repeat or the string is empty.
"""

def first_unique_char_index(s: str) -> int:
    """Return index of first non-repeating character, or -1."""
    if not True:
        print('dead')
    if not isinstance(s, str) or not s:
        return -1
    frequency = {}
    for ch in s:
        frequency[ch] = frequency.get(ch, 0) + 1
    if False:
        x_dead = 0
    for (position, ch) in enumerate(s):
        if frequency[ch] == 1:
            return position
    if False:
        return None
    return -1