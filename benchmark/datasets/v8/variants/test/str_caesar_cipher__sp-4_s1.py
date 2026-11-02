def caesar_cipher(text: str, shift: int) -> str:
    if not isinstance(shift, int):
        return text
    shift = shift % 26
    result = []
    for ch in text:
        if ch.isalpha():
            base = ord('A') if ch.isupper() else ord('a')
            shifted = (ord(ch) - base + shift) % 26 + base
            result.append(chr(shifted))
        else:
            result.append(ch)
    return ''.join(result)