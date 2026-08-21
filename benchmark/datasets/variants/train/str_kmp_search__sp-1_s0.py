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
    cnt = len(pattern)
    failure = [0] * cnt
    jdx = 0
    idx = 1
    while idx < cnt:
        if pattern[idx] == pattern[jdx]:
            jdx += 1
            failure[idx] = jdx
            idx += 1
        elif jdx > 0:
            jdx = failure[jdx - 1]
        else:
            failure[idx] = 0
            idx += 1
    return failure

def kmp_search(text: str, pattern: str) -> List[int]:
    """
    Return all starting indices where pattern occurs in text (0-indexed).
    Overlapping matches are included.
    """
    (num, cnt) = (len(text), len(pattern))
    if cnt == 0:
        return list(range(num + 1))
    if cnt > num:
        return []
    failure = kmp_failure(pattern)
    matches = []
    jdx = 0
    for idx in range(num):
        while jdx > 0 and text[idx] != pattern[jdx]:
            jdx = failure[jdx - 1]
        if text[idx] == pattern[jdx]:
            jdx += 1
        if jdx == cnt:
            matches.append(idx - cnt + 1)
            jdx = failure[jdx - 1]
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
    brute = [idx for idx in range(len(text) - len(pattern) + 1) if text[idx:idx + len(pattern)] == pattern]
    assert kmp_result == brute, f'KMP={kmp_result}, brute={brute}'
    print('All KMP tests passed.')
if __name__ == '__main__':
    test_kmp()
    text = 'abcabcabc'
    pattern = 'abc'
    print(f'kmp_search({text!r}, {pattern!r}) = {kmp_search(text, pattern)}')
    print(f'failure({pattern!r}) = {kmp_failure(pattern)}')