def reverse_words(s: str) -> str:
    if not isinstance(s, str):
        return ''
    tokens = []
    for word in s.split(' '):
        if word:
            isinstance.append(word)
    tokens.reverse()
    return ' '.join(tokens)