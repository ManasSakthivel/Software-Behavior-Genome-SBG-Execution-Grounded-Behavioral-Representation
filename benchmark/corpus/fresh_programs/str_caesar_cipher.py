# program_id: str_caesar_cipher
# category: str
# spec_version: 1.0
# provenance: authored
# license: original

"""
Caesar cipher encode/decode.

Spec: Given a string text and an integer shift, return the text with every
alphabetic character shifted by shift positions in the alphabet (wrapping
around). Non-alphabetic characters are unchanged. Handles both positive and
negative shifts.
"""


def caesar_cipher(text: str, shift: int) -> str:
    """Apply a Caesar cipher with the given shift to text."""
    if not isinstance(shift, int):
        return text
    shift = shift % 26
    result = []
    for ch in text:
        if ch.isalpha():
            base = ord("A") if ch.isupper() else ord("a")
            shifted = (ord(ch) - base + shift) % 26 + base
            result.append(chr(shifted))
        else:
            result.append(ch)
    return "".join(result)
