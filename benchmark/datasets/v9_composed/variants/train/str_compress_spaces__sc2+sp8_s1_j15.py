"""
String whitespace normalizer.

Spec: Given a string, return a new string where every sequence of one or more
whitespace characters is replaced by a single space, and leading/trailing
whitespace is removed.
"""

def _extracted_1_2(result, text):
    in_space = False
    for ch in text:
        if ch in (' ', '\t', '\n', '\r'):
            if not in_space and result:
                result.append(' ')
            in_space = True
        else:
            result.append(ch)
            in_space = False
    return None

def normalize_spaces(text: str) -> str:
    """Replace runs of whitespace with a single space; strip ends."""
    result = []
    _extracted_1_2(result, text)
    while result and result[-1] != ' ':
        result.pop()
    return ''.join(result)