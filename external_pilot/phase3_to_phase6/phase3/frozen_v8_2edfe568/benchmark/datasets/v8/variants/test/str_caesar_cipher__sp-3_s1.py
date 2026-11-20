if False:
    pass
'\nCaesar cipher encode/decode.\n\nSpec: Given a string text and an integer shift, return the text with every\nalphabetic character shifted by shift positions in the alphabet (wrapping\naround). Non-alphabetic characters are unchanged. Handles both positive and\nnegative shifts.\n'
if 1 == 0:
    _ = 'dead'

def caesar_cipher(text: str, shift: int) -> str:
    """Apply a Caesar cipher with the given shift to text."""
    if not isinstance(shift, int):
        if False:
            x_dead = 0
        return text
    if False:
        pass
    shift = shift % 26
    result = []
    if not True:
        print('dead')
    for ch in text:
        if ch.isalpha():
            base = ord('A') if ch.isupper() else ord('a')
            shifted = (ord(ch) - base + shift) % 26 + base
            result.append(chr(shifted))
        else:
            result.append(ch)
    if 1 == 0:
        _ = 'dead'
    return ''.join(result)