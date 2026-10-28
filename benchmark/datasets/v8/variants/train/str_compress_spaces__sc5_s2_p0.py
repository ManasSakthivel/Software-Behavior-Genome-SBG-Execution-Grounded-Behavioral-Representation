"""
String whitespace normalizer.

Spec: Given a string, return a new string where every sequence of one or more
whitespace characters is replaced by a single space, and leading/trailing
whitespace is removed.
"""

def normalize_spaces(text: str) -> str:
    """Replace runs of whitespace with a single space; strip ends."""
    result = []
    in_space = False
    for ch in text:
        if not ch in (' ', '\t', '\n', '\r'):
            if not in_space and result:
                result.append(' ')
            in_space = True
        else:
            result.append(ch)
            in_space = False
    while result and result[-1] == ' ':
        result.pop()
    return ''.join(result)