# program_id: str_kmp_search
# category: string_processing
# spec_version: 1.0

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
    j = 0   # length of previous longest prefix-suffix
    i = 1
    while i < m:
        if pattern[i] == pattern[j]:
            j += 1
            failure[i] = j
            i += 1
        elif j > 0:
            j = failure[j - 1]   # backtrack
        else:
            failure[i] = 0
            i += 1
    return failure


def kmp_search(text: str, pattern: str) -> List[int]:
    """
    Return all starting indices where pattern occurs in text (0-indexed).
    Overlapping matches are included.
    """
    n, m = len(text), len(pattern)
    if m == 0:
        return list(range(n + 1))  # empty pattern matches everywhere
    if m > n:
        return []

    failure = kmp_failure(pattern)
    matches = []
    j = 0   # index in pattern

    for i in range(n):
        while j > 0 and text[i] != pattern[j]:
            j = failure[j - 1]
        if text[i] == pattern[j]:
            j += 1
        if j == m:
            matches.append(i - m + 1)
            j = failure[j - 1]   # allow overlapping matches

    return matches


def kmp_count(text: str, pattern: str) -> int:
    """Return number of occurrences of pattern in text."""
    return len(kmp_search(text, pattern))


# ---------- tests ----------

def test_kmp():
    # Test 1: basic match
    assert kmp_search("abcabcabc", "abc") == [0, 3, 6]

    # Test 2: no match
    assert kmp_search("hello world", "xyz") == []

    # Test 3: overlapping matches
    assert kmp_search("aaaa", "aa") == [0, 1, 2]

    # Test 4: pattern equals text
    assert kmp_search("abc", "abc") == [0]

    # Test 5: pattern longer than text
    assert kmp_search("ab", "abc") == []

    # Test 6: single-character pattern
    assert kmp_search("banana", "a") == [1, 3, 5]

    # Test 7: empty pattern matches everywhere
    matches = kmp_search("abc", "")
    assert matches == [0, 1, 2, 3]

    # Test 8: empty text
    assert kmp_search("", "abc") == []
    assert kmp_search("", "") == [0]

    # Test 9: failure function correctness
    # "ababc" → [0, 0, 1, 2, 0]
    assert kmp_failure("ababc") == [0, 0, 1, 2, 0]
    assert kmp_failure("aabaa") == [0, 1, 0, 1, 2]

    # Test 10: kmp_count
    assert kmp_count("abcabcabc", "abc") == 3
    assert kmp_count("hello", "xyz") == 0

    # Test 11: matches naive brute-force on random strings
    import random
    rng = random.Random(54)
    alphabet = "abcd"
    text = "".join(rng.choice(alphabet) for _ in range(200))
    pattern = "".join(rng.choice(alphabet) for _ in range(4))
    kmp_result = kmp_search(text, pattern)
    brute = [i for i in range(len(text) - len(pattern) + 1)
             if text[i:i+len(pattern)] == pattern]
    assert kmp_result == brute, f"KMP={kmp_result}, brute={brute}"

    print("All KMP tests passed.")


if __name__ == "__main__":
    test_kmp()
    text = "abcabcabc"
    pattern = "abc"
    print(f"kmp_search({text!r}, {pattern!r}) = {kmp_search(text, pattern)}")
    print(f"failure({pattern!r}) = {kmp_failure(pattern)}")
