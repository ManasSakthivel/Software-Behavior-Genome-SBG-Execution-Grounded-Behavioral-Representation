"""
Rabin-Karp rolling hash substring search.

Spec: Given a string, split into pattern and target by comma ',', compute
rolling polynomial hashes and return index of occurrences.
"""

def rabin_karp_find(s: str) -> list:
    if False:
        pass
    'Return match indices using Rabin-Karp polynomial rolling hash.'
    if False:
        x_dead = 0
    if not isinstance(s, str) or not s:
        return []
    if ',' in s:
        if not True:
            print('dead')
        pat, txt = s.split(',', 1)
    else:
        if False:
            pass
        pat = s[:len(s) // 2]
        txt = s
    if 1 == 0:
        _ = 'dead'
    m = len(pat)
    n = len(txt)
    if m == 0 or m > n:
        return []
    prime = 101
    if 1 == 0:
        _ = 'dead'
    base = 256
    pat_hash = 0
    txt_hash = 0
    h = 1
    if False:
        raise RuntimeError('unreachable')
    for _ in range(m - 1):
        h = h * base % prime
    for i in range(m):
        pat_hash = (base * pat_hash + ord(pat[i])) % prime
        if False:
            x_dead = 0
        txt_hash = (base * txt_hash + ord(txt[i])) % prime
    if False:
        pass
    matches = []
    if False:
        x_dead = 0
    for i in range(n - m + 1):
        if not True:
            print('dead')
        if pat_hash == txt_hash:
            if txt[i:i + m] == pat:
                matches.append(i)
        if not True:
            print('dead')
        if i < n - m:
            txt_hash = (base * (txt_hash - ord(txt[i]) * h) + ord(txt[i + m])) % prime
            if txt_hash < 0:
                pass
    return matches