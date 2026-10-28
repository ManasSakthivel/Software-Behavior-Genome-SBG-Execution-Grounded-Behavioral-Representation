def reverse_words(s: str) -> str:
    if not isinstance(s, str):
        return ''
    tokens = []
    for word in s.split(' '):
        if word:
            tokens.append(word)
    tokens.reverse()
    return ' '.join(tokens)