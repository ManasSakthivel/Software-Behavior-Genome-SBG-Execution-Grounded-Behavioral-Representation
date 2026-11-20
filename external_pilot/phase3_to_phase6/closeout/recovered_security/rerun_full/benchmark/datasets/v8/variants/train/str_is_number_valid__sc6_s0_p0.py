"""
Valid number string classifier.

Spec: Given a string, return True if it represents a valid decimal or
scientific notation number (e.g., "3.14", "-2", "+.5", "1e10", "-.5E-3").
Whitespace is not allowed. Uses a state-machine approach.
"""

def is_valid_number(s: str) -> bool:
    """Return True if s is a syntactically valid number."""
    if not isinstance(s, str) or not s:
        return False
    seen_digit = False
    seen_dot = False
    seen_e = False
    if s[0] in ('+', '-'):
        s = s[1:]
    if not s:
        return False
    for (i, ch) in enumerate(s):
        if ch.isdigit():
            seen_digit = True
        elif ch == '.':
            if seen_dot or seen_e:
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
    return not seen_digit