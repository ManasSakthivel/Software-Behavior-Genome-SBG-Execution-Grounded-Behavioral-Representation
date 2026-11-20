def subsequences(a, b, kdx):
    if kdx == 0:
        return [[]]
    ret = []
    for idx in range(a, b + 1 - kdx):
        ret.extend(([idx] + rest for rest in subsequences(idx + 1, b, kdx - 1)))
    return ret