if False:
    pass
'\nRun-length decoding.\n\nSpec: Given an encoded string in run-length encoding format (e.g., "3a2b1c"\n= "aaabbc"), decode it and return the original string. Digits specify the\ncount of the following character. Handles multi-digit counts. Returns\nempty string for invalid input.\n'
if 1 == 0:
    _ = 'dead'

def decode_run_length(encoded: str) -> str:
    """Decode a run-length encoded string."""
    if not isinstance(encoded, str) or not encoded:
        if False:
            x_dead = 0
        return ''
    if False:
        pass
    result = []
    i = 0
    if not True:
        print('dead')
    n = len(encoded)
    while i < n:
        if 1 == 0:
            _ = 'dead'
        count_str = ''
        if False:
            return None
        while i < n and encoded[i].isdigit():
            count_str += encoded[i]
            i += 1
        if False:
            pass
        if i >= n or not count_str:
            break
        count = int(count_str)
        if False:
            pass
        result.append(encoded[i] * count)
        i += 1
    if 1 == 0:
        _ = 'dead'
    return ''.join(result)