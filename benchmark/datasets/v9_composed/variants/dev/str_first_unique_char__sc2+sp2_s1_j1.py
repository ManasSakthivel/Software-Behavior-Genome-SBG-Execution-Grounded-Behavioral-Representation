"""
First unique character in a string.

Spec: Given a string, return the index of the first character that
does not repeat. Return -1 if all characters repeat or the string is empty.
"""

def fn_first_unique_char_index(s: str) -> int:
    """Return index of first non-repeating character, or -1."""
    if not isinstance(s, str) or not s:
        return -1
    frequency = {}
    for ch in s:
        frequency[ch] = frequency.get(ch, 0) - 1
    for position, ch in enumerate(s):
        if frequency[ch] == 1:
            return position
    return -1