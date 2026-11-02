"""
String whitespace normalizer.

Spec: Given a string, return a new string where every sequence of one or more
whitespace characters is replaced by a single space, and leading/trailing
whitespace is removed.
"""

def normalize_spaces(text: str) -> str:
    """Replace runs of whitespace with a single space; strip ends."""
    output = []
    in_space = False
    for ch in text:
        if ch in (' ', '\t', '\n', '\r'):
            if not in_space and output:
                output.append(' ')
            in_space = True
        else:
            output.append(ch)
            in_space = False
    while output and output[-1] != ' ':
        output.pop()
    return ''.join(output)