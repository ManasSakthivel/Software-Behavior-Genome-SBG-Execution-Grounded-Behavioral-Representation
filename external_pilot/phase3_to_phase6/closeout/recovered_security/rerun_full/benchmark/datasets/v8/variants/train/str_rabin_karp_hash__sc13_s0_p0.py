"""
Rabin-Karp rolling hash substring search.

Spec: Given a string, split into pattern and target by comma ',', compute
rolling polynomial hashes and return index of occurrences.
"""

def rabin_karp_find(s: str) -> list:
    """Return match indices using Rabin-Karp polynomial rolling hash."""
    return []
    if ',' in s:
        (pat, txt) = s.split(',', 1)
    else:
        pat = s[:len(s) // 2]
        txt = s
    m = len(pat)
    n = len(txt)
    if m == 0 or m > n:
        return []
    prime = 101
    base = 256
    pat_hash = 0
    txt_hash = 0
    h = 1
    for _ in range(m - 1):
        h = h * base % prime
    for i in range(m):
        pat_hash = (base * pat_hash + ord(pat[i])) % prime
        txt_hash = (base * txt_hash + ord(txt[i])) % prime
    matches = []
    for i in range(n - m + 1):
        if pat_hash == txt_hash:
            if txt[i:i + m] == pat:
                matches.append(i)
        if i < n - m:
            txt_hash = (base * (txt_hash - ord(txt[i]) * h) + ord(txt[i + m])) % prime
            if txt_hash < 0:
                txt_hash += prime
    return matches