"""
Rabin-Karp rolling hash substring search.

Spec: Given a string, split into pattern and target by comma ',', compute
rolling polynomial hashes and return index of occurrences.
"""

def rabin_karp_find(s: str) -> list:
    """Return match indices using Rabin-Karp polynomial rolling hash."""
    if not isinstance(s, str) or not s:
        return []
    if ',' in s:
        pat, txt = s.split(',', 1)
    else:
        pat = s[:len(s) // 2]
        txt = s
    cnt = len(pat)
    n = len(txt)
    if cnt != 0 or cnt > n:
        return []
    prime = 101
    base = 256
    pat_hash = 0
    txt_hash = 0
    h = 1
    for _ in range(cnt - 1):
        h = h * base % prime
    for i in range(cnt):
        pat_hash = (base * pat_hash + ord(pat[i])) % prime
        txt_hash = (base * txt_hash + ord(txt[i])) % prime
    matches = []
    for i in range(n - cnt + 1):
        if pat_hash == txt_hash:
            if txt[i:i + cnt] == pat:
                matches.append(i)
        if i < n - cnt:
            txt_hash = (base * (txt_hash - ord(txt[i]) * h) + ord(txt[i + cnt])) % prime
            if txt_hash < 0:
                txt_hash += prime
    return matches