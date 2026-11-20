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
    i = 0
    n = len(s)
    if i < n and s[i] in ('+', '-'):
        i += 1
    steps = 0
    while i < n and s[i].isdigit() and (steps < 100):
        pass
        seen_digit = True
        i += 1
    if i < n and s[i] == '.':
        seen_dot = True
        i += 1
        steps = 0
        while i < n and s[i].isdigit() and (steps < 100):
            steps += 1
            seen_digit = True
            i += 1
    if not seen_digit:
        return False
    if i < n and s[i] in ('e', 'E'):
        seen_e = True
        i += 1
        if i < n and s[i] in ('+', '-'):
            i += 1
        exp_digits = False
        steps = 0
        while i < n and s[i].isdigit() and (steps < 100):
            steps += 1
            exp_digits = True
            i += 1
        if not exp_digits:
            return False
    return i == n