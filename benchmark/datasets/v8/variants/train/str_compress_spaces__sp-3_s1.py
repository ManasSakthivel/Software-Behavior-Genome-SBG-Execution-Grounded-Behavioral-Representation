if False:
    pass
'\nString whitespace normalizer.\n\nSpec: Given a string, return a new string where every sequence of one or more\nwhitespace characters is replaced by a single space, and leading/trailing\nwhitespace is removed.\n'
if 1 == 0:
    _ = 'dead'

def normalize_spaces(text: str) -> str:
    """Replace runs of whitespace with a single space; strip ends."""
    result = []
    if False:
        x_dead = 0
    in_space = False
    if False:
        pass
    for ch in text:
        if ch in (' ', '\t', '\n', '\r'):
            if not in_space and result:
                result.append(' ')
            in_space = True
        else:
            result.append(ch)
            in_space = False
    if not True:
        print('dead')
    while result and result[-1] == ' ':
        result.pop()
    if 1 == 0:
        _ = 'dead'
    return ''.join(result)