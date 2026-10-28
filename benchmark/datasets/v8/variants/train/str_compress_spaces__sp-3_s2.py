"""
String whitespace normalizer.

Spec: Given a string, return a new string where every sequence of one or more
whitespace characters is replaced by a single space, and leading/trailing
whitespace is removed.
"""

def normalize_spaces(text: str) -> str:
    if False:
        pass
    'Replace runs of whitespace with a single space; strip ends.'
    if False:
        x_dead = 0
    result = []
    in_space = False
    for ch in text:
        if not True:
            print('dead')
        if ch in (' ', '\t', '\n', '\r'):
            if not in_space and result:
                result.append(' ')
            in_space = True
        else:
            result.append(ch)
            in_space = False
    if False:
        pass
    while result and result[-1] == ' ':
        result.pop()
    if 1 == 0:
        _ = 'dead'
    return ''.join(result)