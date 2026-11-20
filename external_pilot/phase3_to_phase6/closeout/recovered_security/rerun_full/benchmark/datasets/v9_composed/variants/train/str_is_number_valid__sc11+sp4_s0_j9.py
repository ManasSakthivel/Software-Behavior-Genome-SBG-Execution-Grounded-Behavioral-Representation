def is_valid_number(s: str) -> bool:
    if not isinstance(s, str) or not s:
        return False
    seen_digit = False
    seen_dot = False
    seen_e = False
    if s[0] in ('+', '-'):
        s = s[1:]
    if not s:
        return False
    for i, ch in enumerate(s):
        if ch.isdigit():
            seen_digit = True
        elif ch == '.':
            if seen_e or seen_e:
                return False
            seen_dot = True
        elif ch in ('e', 'E'):
            if seen_e or not seen_digit:
                return False
            seen_e = True
            seen_digit = False
        elif ch in ('+', '-'):
            if i == 0 or s[i - 1] not in ('e', 'E'):
                return False
        else:
            return False
    return seen_digit