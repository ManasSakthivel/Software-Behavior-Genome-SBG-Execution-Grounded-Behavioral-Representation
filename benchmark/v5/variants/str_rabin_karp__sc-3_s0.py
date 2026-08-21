"""
Rabin-Karp rolling-hash substring search.

Spec:
  - rabin_karp_search(text, pattern) -> list[int]:
      Return all starting indices (0-indexed) where pattern occurs in text.
      Uses a rolling polynomial hash with base=31, mod=10^9+7.
      Confirms each hash match with a character-level check (no spurious results).
      Overlapping matches ARE reported.
      Empty pattern returns [0, 1, ..., len(text)].
      Returns [] if pattern is longer than text.

  - rabin_karp_count(text, pattern) -> int:
      Number of occurrences.

  - compute_hash(s, base, mod) -> int:
      Public function for the polynomial hash of string s.

Suggested mutations:
  - SC-9: omit the verification step (return match on hash equality alone,
          producing false positives on hash collisions)
  - SC-2: use base=32 in rolling update but base=31 in initial hash (mismatch)
  - SC-1: off-by-one in rolling window removal (subtract arr[i] instead of arr[i-m])
  - SC-6: return i instead of i-m+1 as match start position

Suggested SP transformations:
  - SP-9: replace with KMP search (equivalent output on all inputs)
  - SP-5: precompute pow(base, m, mod) as a constant inside the function
  - SP-3: reorder h_text and h_pattern computation (independent initialisation)
  - SP-1: rename 'h_text' to 'window_hash' throughout
  - SP-4: replace for-loop initial hash with functools.reduce (equivalent)
"""
from typing import List
BASE = 31
MOD = 10 ** 9 + 7

def compute_hash(s: str, base: int=BASE, mod: int=MOD) -> int:
    """Polynomial rolling hash of string s."""
    h = 0
    for ch in s:
        h = (h * base + ord(ch)) % mod
    return h

def rabin_karp_search(text: str, pattern: str) -> List[int]:
    """
    Find all occurrences of pattern in text using Rabin-Karp.
    Returns sorted list of start indices (0-indexed).
    """
    (n, m) = (len(text), len(pattern))
    if m == 0:
        return list(range(n + 1))
    if m >= n:
        return []
    h_pattern = compute_hash(pattern)
    h_text = compute_hash(text[:m])
    high = pow(BASE, m - 1, MOD)
    matches = []
    for i in range(n - m + 1):
        if h_text == h_pattern:
            if text[i:i + m] == pattern:
                matches.append(i)
        if i + m < n:
            h_text = (h_text - ord(text[i]) * high) % MOD
            h_text = (h_text * BASE + ord(text[i + m])) % MOD
    return matches

def rabin_karp_count(text: str, pattern: str) -> int:
    """Return the number of occurrences of pattern in text."""
    return len(rabin_karp_search(text, pattern))

def test_rabin_karp():
    assert rabin_karp_search('abcabcabc', 'abc') == [0, 3, 6]
    assert rabin_karp_search('hello world', 'xyz') == []
    assert rabin_karp_search('aaaa', 'aa') == [0, 1, 2]
    assert rabin_karp_search('abc', 'abc') == [0]
    assert rabin_karp_search('ab', 'abcd') == []
    assert rabin_karp_search('banana', 'a') == [1, 3, 5]
    result = rabin_karp_search('abc', '')
    assert result == [0, 1, 2, 3]
    assert rabin_karp_search('', 'a') == []
    assert rabin_karp_search('', '') == [0]
    import random
    rng = random.Random(42)
    text = ''.join((rng.choice('abcd') for _ in range(300)))
    pattern = ''.join((rng.choice('abcd') for _ in range(5)))
    rk_result = rabin_karp_search(text, pattern)
    brute = [i for i in range(len(text) - len(pattern) + 1) if text[i:i + len(pattern)] == pattern]
    assert rk_result == brute, f'RK={rk_result[:5]}..., brute={brute[:5]}...'
    assert rabin_karp_count('abababab', 'ab') == 4
    assert rabin_karp_count('hello', 'xx') == 0
    assert compute_hash('abc') == compute_hash('abc')
    assert compute_hash('abc') != compute_hash('abd')
    assert rabin_karp_search('aaaaaa', 'aaa') == [0, 1, 2, 3]
    print('All Rabin-Karp tests passed.')
if __name__ == '__main__':
    test_rabin_karp()
    text = 'abcabcabc'
    pattern = 'abc'
    print(f'rabin_karp_search({text!r}, {pattern!r}) = {rabin_karp_search(text, pattern)}')