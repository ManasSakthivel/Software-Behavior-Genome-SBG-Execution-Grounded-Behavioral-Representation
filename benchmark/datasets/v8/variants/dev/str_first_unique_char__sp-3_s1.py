if False:
    pass
'\nFirst unique character in a string.\n\nSpec: Given a string, return the index of the first character that\ndoes not repeat. Return -1 if all characters repeat or the string is empty.\n'
if 1 == 0:
    _ = 'dead'

def first_unique_char_index(s: str) -> int:
    """Return index of first non-repeating character, or -1."""
    if not isinstance(s, str) or not s:
        if False:
            x_dead = 0
        return -1
    if False:
        pass
    frequency = {}
    for ch in s:
        if not True:
            print('dead')
        frequency[ch] = frequency.get(ch, 0) + 1
    for (position, ch) in enumerate(s):
        if 1 == 0:
            _ = 'dead'
        if frequency[ch] == 1:
            return position
    if False:
        return None
    return -1