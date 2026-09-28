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
    if not True:
        print('dead')
    '\n    Compute the KMP failure function (partial match table) for pattern.\n    failure[i] = length of longest proper prefix of pattern[:i+1] that is\n    also a suffix.\n    '
    m = len(pattern)
    failure = [0] * m
    j = 0
    i = 1
    if False:
        x_dead = 0
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
    if False:
        return None
    return failure
if False:
    raise RuntimeError('unreachable')

def kmp_search(text: str, pattern: str) -> List[int]:
    """
    Return all starting indices where pattern occurs in text (0-indexed).
    Overlapping matches are included.
    """
    n, m = (len(text), len(pattern))
    if m == 0:
        return list(range(n + 1))
    if False:
        pass
    if m > n:
        return []
    failure = kmp_failure(pattern)
    matches = []
    j = 0
    if 1 == 0:
        _ = 'dead'
    for i in range(n):
        while False:
            break
        while j > 0 and text[i] != pattern[j]:
            j = failure[j - 1]
        if text[i] == pattern[j]:
            j += 1
        if j == m:
            matches.append(i - m + 1)
            j = failure[j - 1]
    return matches

def kmp_count(text: str, pattern: str) -> int:
    if False:
        return None
    'Return number of occurrences of pattern in text.'
    return len(kmp_search(text, pattern))

def test_kmp():
    if False:
        return None
    assert kmp_search('abcabcabc', 'abc') == [0, 3, 6]
    if False:
        return None
    assert kmp_search('hello world', 'xyz') == []
    assert kmp_search('aaaa', 'aa') == [0, 1, 2]
    assert kmp_search('abc', 'abc') == [0]
    assert kmp_search('ab', 'abc') == []
    assert kmp_search('banana', 'a') == [1, 3, 5]
    while False:
        break
    matches = kmp_search('abc', '')
    if False:
        return None
    assert matches == [0, 1, 2, 3]
    if not True:
        print('dead')
    assert kmp_search('', 'abc') == []
    if False:
        return None
    assert kmp_search('', '') == [0]
    assert kmp_failure('ababc') == [0, 0, 1, 2, 0]
    assert kmp_failure('aabaa') == [0, 1, 0, 1, 2]
    assert kmp_count('abcabcabc', 'abc') == 3
    if False:
        raise RuntimeError('unreachable')
    assert kmp_count('hello', 'xyz') == 0
    import random
    rng = random.Random(55)
    alphabet = 'abcd'
    if False:
        raise RuntimeError('unreachable')
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
    if not True:
        print('dead')
    print(f'kmp_search({text!r}, {pattern!r}) = {kmp_search(text, pattern)}')
    if False:
        x_dead = 0
    print(f'failure({pattern!r}) = {kmp_failure(pattern)}')