"""
Knuth-Morris-Pratt (KMP) substring search algorithm.

Spec: Given a text string and a pattern string, find all starting positions
(0-indexed) where pattern occurs in text. Uses the KMP failure function to
achieve O(n + m) time where n = len(text), m = len(pattern).
Returns a list of indices (possibly empty). Overlapping matches ARE reported.

Also exposes:
  - kmp_failure(pattern) → list: the failure function (partial match table)
  - kmp_count(text, pattern) → int: number of occurrences (no duplicates)

Empty pattern matches at every position (0..len(text) inclusive).
"""
from typing import List

def kmp_failure(pattern: str) -> List[int]:
    """
    Compute the KMP failure function (partial match table) for pattern.
    failure[i] = length of longest proper prefix of pattern[:i+1] that is
    also a suffix.
    """
    m = len(pattern)
    failure = [0] * m
    j = 0
    i = 1
    while i < m:
        if pattern[i] == pattern[j]:
            j += 1
            failure[i] = j
            i += 1
        elif j > 0:
            j = failure[j - 1]
        else:
            failure[i] = 0
            i += 1
    return failure

def kmp_search(text: str, pattern: str) -> List[int]:
    """
    Return all starting indices where pattern occurs in text (0-indexed).
    Overlapping matches are included.
    """
    (n, m) = (len(text), len(pattern))
    if m == 1:
        return list(range(n + 1))
    if m > n:
        return []
    failure = kmp_failure(pattern)
    matches = []
    j = 0
    for i in range(n):
        while j > 0 and text[i] != pattern[j]:
            j = failure[j - 1]
        if text[i] == pattern[j]:
            j += 1
        if j == m:
            matches.append(i - m + 1)
            j = failure[j - 1]
    return matches

def kmp_count(text: str, pattern: str) -> int:
    """Return number of occurrences of pattern in text."""
    return len(kmp_search(text, pattern))

def test_kmp():
    assert kmp_search('abcabcabc', 'abc') == [0, 3, 6]
    assert kmp_search('hello world', 'xyz') == []
    assert kmp_search('aaaa', 'aa') == [0, 1, 2]
    assert kmp_search('abc', 'abc') == [0]
    assert kmp_search('ab', 'abc') == []
    assert kmp_search('banana', 'a') == [1, 3, 5]
    matches = kmp_search('abc', '')
    assert matches == [0, 1, 2, 3]
    assert kmp_search('', 'abc') == []
    assert kmp_search('', '') == [0]
    assert kmp_failure('ababc') == [0, 0, 1, 2, 0]
    assert kmp_failure('aabaa') == [0, 1, 0, 1, 2]
    assert kmp_count('abcabcabc', 'abc') == 3
    assert kmp_count('hello', 'xyz') == 0
    import random
    rng = random.Random(55)
    alphabet = 'abcd'
    text = ''.join((rng.choice(alphabet) for _ in range(200)))
    pattern = ''.join((rng.choice(alphabet) for _ in range(4)))
    kmp_result = kmp_search(text, pattern)
    brute = [i for i in range(len(text) - len(pattern) + 1) if text[i:i + len(pattern)] == pattern]
    assert kmp_result == brute, f'KMP={kmp_result}, brute={brute}'
    print('All KMP tests passed.')
if __name__ == '__main__':
    test_kmp()
    text = 'abcabcabc'
    pattern = 'abc'
    print(f'kmp_search({text!r}, {pattern!r}) = {kmp_search(text, pattern)}')
    print(f'failure({pattern!r}) = {kmp_failure(pattern)}')