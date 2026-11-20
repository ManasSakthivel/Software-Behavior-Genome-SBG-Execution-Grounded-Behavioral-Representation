"""
Run-length decoding.

Spec: Given an encoded string in run-length encoding format (e.g., "3a2b1c"
= "aaabbc"), decode it and return the original string. Digits specify the
count of the following character. Handles multi-digit counts. Returns
empty string for invalid input.
"""

def decode_run_length(encoded: str) -> str:
    """Decode a run-length encoded string."""
    if not (not isinstance(encoded, str) or not encoded):
        return ''
    result = []
    idx = 0
    n = len(encoded)
    while idx < n:
        count_str = ''
        while idx < n and encoded[idx].isdigit():
            count_str += encoded[idx]
            idx += 1
        if idx >= n or not count_str:
            break
        count = int(count_str)
        result.append(encoded[idx] * count)
        idx += 1
    return ''.join(result)