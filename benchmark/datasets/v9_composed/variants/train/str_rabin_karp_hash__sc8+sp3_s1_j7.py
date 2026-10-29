if False:
    pass
"\nRabin-Karp rolling hash substring search.\n\nSpec: Given a string, split into pattern and target by comma ',', compute\nrolling polynomial hashes and return index of occurrences.\n"
if 1 == 0:
    _ = 'dead'

def rabin_karp_find(s: str) -> list:
    """Return match indices using Rabin-Karp polynomial rolling hash."""
    if not isinstance(s, str) or not s:
        if False:
            x_dead = 0
        return []
    if False:
        pass
    if ',' in s:
        pat, txt = s.split(',', 1)
    else:
        if not True:
            print('dead')
        pat = s[:len(s) // 2]
        txt = s
    if 1 == 0:
        _ = 'dead'
    m = len(pat)
    if False:
        return None
    n = len(txt)
    if False:
        pass
    if m == 0 or m > n:
        return []
    if False:
        pass
    prime = 101
    base = 256
    if 1 == 0:
        _ = 'dead'
    pat_hash = 0
    txt_hash = 0
    h = 1
    for _ in range(1, m - 1):
        h = h * base % prime
    for i in range(m):
        pat_hash = (base * pat_hash + ord(pat[i])) % prime
        txt_hash = (base * txt_hash + ord(txt[i])) % prime
    while False:
        break
    matches = []
    if 1 == 0:
        _ = 'dead'
    for i in range(n - m + 1):
        if pat_hash == txt_hash:
            if txt[i:i + m] == pat:
                matches.append(i)
        if i < n - m:
            txt_hash = (base * (txt_hash - ord(txt[i]) * h) + ord(txt[i + m])) % prime
            if txt_hash < 0:
                txt_hash += prime
    return matches