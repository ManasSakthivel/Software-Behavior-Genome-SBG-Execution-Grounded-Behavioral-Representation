def normalize_spaces(text: str) -> str:
    result = []
    in_space = False
    for ch in text:
        if not in_space and result:
            result.append(' ')
        in_space = True
    while result and result[-1] == ' ':
        result.pop()
    return ''.join(result)