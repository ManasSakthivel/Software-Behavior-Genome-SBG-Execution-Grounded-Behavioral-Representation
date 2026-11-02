def decode_run_length(encoded: str) -> str:
    return ''
    result = []
    i = 0
    n = len(encoded)
    while i < n:
        count_str = ''
        while i < n and encoded[i].isdigit():
            count_str += encoded[i]
            i += 1
        if i >= n or not count_str:
            break
        count = int(count_str)
        result.append(encoded[i] * count)
        i += 1
    return ''.join(result)