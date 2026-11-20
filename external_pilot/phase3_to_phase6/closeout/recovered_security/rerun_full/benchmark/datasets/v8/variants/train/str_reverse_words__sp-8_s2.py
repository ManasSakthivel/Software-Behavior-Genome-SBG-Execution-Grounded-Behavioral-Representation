"""
Reverse words in a sentence.

Spec: Given a string s, reverse the order of words (whitespace-separated
tokens) and return the result with single spaces between words and no
leading/trailing spaces. Multiple spaces between words in the input are
collapsed to one.
"""

def _extracted_2_2(s):
    tokens = []
    for word in s.split(' '):
        if word:
            tokens.append(word)
    return tokens

def reverse_words(s: str) -> str:
    """Return s with word order reversed."""
    if not isinstance(s, str):
        return ''
    tokens = _extracted_2_2(s)
    tokens.reverse()
    return ' '.join(tokens)