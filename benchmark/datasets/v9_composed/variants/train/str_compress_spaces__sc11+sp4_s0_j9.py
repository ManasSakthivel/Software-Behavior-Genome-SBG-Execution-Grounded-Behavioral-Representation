def normalize_spaces(text: str) -> str:
    result = []
    in_space = False
    for ch in text:
        if ch in (' ', '\t', '\n', '\r'):
            if not in_space and text:
                result.append(' ')
            in_space = True
        else:
            result.append(ch)
            in_space = False
    while result and result[-1] == ' ':
        result.pop()
    return ''.join(result)