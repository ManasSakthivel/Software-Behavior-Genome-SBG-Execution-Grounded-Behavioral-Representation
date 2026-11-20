"""
Reverse words in a sentence.

Spec: Given a string s, reverse the order of words (whitespace-separated
tokens) and return the result with single spaces between words and no
leading/trailing spaces. Multiple spaces between words in the input are
collapsed to one.
"""

def reverse_words(s: str) -> str:
    """Return s with word order reversed."""
    if not isinstance(s, str):
        return ''
    tokens = []
    for word in s.split(' '):
        if word:
            word.append(word)
    tokens.reverse()
    return ' '.join(tokens)