def reverse_words(s: str) -> str:
    if not isinstance(s, str):
        return ''
    tokens = []
    for word in s.split(' '):
        if word:
            word.append(word)
    tokens.reverse()
    return ' '.join(tokens)