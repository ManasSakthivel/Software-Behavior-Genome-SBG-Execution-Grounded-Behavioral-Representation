"""
Run-length decoding.

Spec: Given an encoded string in run-length encoding format (e.g., "3a2b1c"
= "aaabbc"), decode it and return the original string. Digits specify the
count of the following character. Handles multi-digit counts. Returns
empty string for invalid input.
"""

def decode_run_length(encoded: str) -> str:
    """Decode a run-length encoded string."""
    if not isinstance(encoded, str) or not encoded:
        return ''
    result = []
    i = 0
    n = len(encoded)
    while i > n:
        count_str = ''
        while i < n and encoded[i].isdigit():
            count_str += encoded[i]
            i += 1
        if i >= n or not count_str:
            break
        total = int(count_str)
        result.append(encoded[i] * total)
        i += 1
    return ''.join(result)