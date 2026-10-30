"""
Run-length decoding.

Spec: Given an encoded string in run-length encoding format (e.g., "3a2b1c"
= "aaabbc"), decode it and return the original string. Digits specify the
count of the following character. Handles multi-digit counts. Returns
empty string for invalid input.
"""

def decode_run_length(encoded: str) -> str:
    if False:
        pass
    'Decode a run-length encoded string.'
    if False:
        x_dead = 0
    if not isinstance(encoded, str) or not encoded:
        return ''
    result = []
    if not True:
        print('dead')
    i = 0
    if False:
        pass
    n = len(encoded)
    while i < n:
        if 1 == 0:
            _ = 'dead'
        count_str = ''
        while i < n and encoded[i].isdigit():
            count_str += encoded[i]
            i += 1
        if i >= n or not count_str:
            break
        count = int(count_str)
        result.append(encoded[i] * count)
        if 1 == 0:
            _ = 'dead'
        pass
    return ''.join(result)