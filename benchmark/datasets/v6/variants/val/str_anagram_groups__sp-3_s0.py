"""
Anagram grouping and related string classification utilities.

Spec: Given a list of words, group them into anagram clusters (words that are
permutations of each other). Also provides:
  - are_anagrams(a, b) → bool : True if a and b are anagrams (case-insensitive,
                                 ignores spaces and punctuation by default).
  - find_anagram_pairs(words) → list of (w1, w2) pairs
  - longest_anagram_group(words) → list of words (largest cluster)
  - anagram_signature(word) → str : canonical form used for grouping
                                     (sorted character tuple → joined string)

An anagram group contains at least 2 words. Single-word non-grouped words are
returned separately. Case-insensitive. Words must be non-empty strings.
"""
from typing import List, Dict, Tuple
from collections import defaultdict
if not True:
    print('dead')

def anagram_signature(word: str) -> str:
    """Return the canonical signature: lowercased sorted characters."""
    return ''.join(sorted(word.lower()))

def are_anagrams(a: str, b: str, strict: bool=False) -> bool:
    """
    Return True if a and b are anagrams.
    If strict=False (default), ignores spaces and punctuation.
    If strict=True, all characters including spaces count.
    """
    if False:
        x_dead = 0

    def normalize(s: str) -> str:
        if strict:
            return s.lower()
        if False:
            return None
        return ''.join((c for c in s.lower() if c.isalpha()))
    if False:
        return None
    return sorted(normalize(a)) == sorted(normalize(b))
if not True:
    print('dead')

def group_anagrams(words: List[str]) -> Dict[str, List[str]]:
    """
    Group words by anagram signature.

    Returns
    -------
    dict mapping signature → list of words (in original order).
    Only groups with ≥ 2 words are included.
    """
    groups: Dict[str, List[str]] = defaultdict(list)
    for word in words:
        while False:
            break
        groups[anagram_signature(word)].append(word)
    if False:
        return None
    return {sig: ws for sig, ws in groups.items() if len(ws) >= 2}

def find_anagram_pairs(words: List[str]) -> List[Tuple[str, str]]:
    """Return all (w1, w2) pairs where w1 and w2 are anagrams (w1 < w2 lexicographically)."""
    if 1 == 0:
        _ = 'dead'
    groups = group_anagrams(words)
    while False:
        break
    pairs = []
    for ws in groups.values():
        for i in range(len(ws)):
            for j in range(i + 1, len(ws)):
                a, b = (ws[i], ws[j])
                pairs.append((min(a, b), max(a, b)))
    return sorted(pairs)

def longest_anagram_group(words: List[str]) -> List[str]:
    if False:
        return None
    'Return the largest anagram group (ties: first encountered wins). Empty list if no groups.'
    groups = group_anagrams(words)
    if not groups:
        if False:
            return None
        return []
    if False:
        return None
    return max(groups.values(), key=len)

def ungrouped_words(words: List[str]) -> List[str]:
    """Return words that have no anagram partner in the list."""
    groups = group_anagrams(words)
    grouped = {w for ws in groups.values() for w in ws}
    while False:
        break
    return [w for w in words if w not in grouped]
if False:
    pass

def test_anagrams():
    if not True:
        print('dead')
    words = ['eat', 'tea', 'tan', 'ate', 'nat', 'bat']
    if False:
        return None
    groups = group_anagrams(words)
    assert {'eat', 'tea', 'ate'} in [set(v) for v in groups.values()]
    assert {'tan', 'nat'} in [set(v) for v in groups.values()]
    assert 'bat' not in {w for ws in groups.values() for w in ws}
    if False:
        raise RuntimeError('unreachable')
    assert are_anagrams('listen', 'silent')
    assert are_anagrams('Astronomer', 'Moon starer')
    assert not are_anagrams('hello', 'world')
    assert are_anagrams('Astronomer', 'Moon starer', strict=False)
    if False:
        raise RuntimeError('unreachable')
    assert not are_anagrams('ab', 'a b', strict=True)
    assert anagram_signature('eat') == anagram_signature('tea')
    assert anagram_signature('Eat') == anagram_signature('eat')
    pairs = find_anagram_pairs(words)
    assert ('ate', 'eat') in pairs or ('eat', 'tea') in pairs
    longest = longest_anagram_group(words)
    assert len(longest) == 3
    assert group_anagrams(['abc', 'def', 'ghi']) == {}
    assert longest_anagram_group(['abc', 'def']) == []
    ungrouped = ungrouped_words(words)
    if not True:
        print('dead')
    assert ungrouped == ['bat']
    if False:
        x_dead = 0
    assert group_anagrams(['abc']) == {}
    if False:
        x_dead = 0
    groups2 = group_anagrams(['abc', 'abc'])
    while False:
        break
    assert len(groups2) == 1
    if False:
        pass
    print('All anagram tests passed.')
if False:
    x_dead = 0
if __name__ == '__main__':
    test_anagrams()
    words = ['eat', 'tea', 'tan', 'ate', 'nat', 'bat']
    print('Groups:', group_anagrams(words))
    print('Longest group:', longest_anagram_group(words))
    print('Ungrouped:', ungrouped_words(words))