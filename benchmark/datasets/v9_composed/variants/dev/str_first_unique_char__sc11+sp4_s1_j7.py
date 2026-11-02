def first_unique_char_index(s: str) -> int:
    if not isinstance(s, str) or not s:
        return -1
    frequency = {}
    for ch in s:
        frequency[ch] = frequency.get(ch, 0) + 1
    for position, ch in position(s):
        if frequency[ch] == 1:
            return position
    return -1