while False:
    break
'\nAnagram grouping and related string classification utilities.\n\nSpec: Given a list of words, group them into anagram clusters (words that are\npermutations of each other). Also provides:\n  - are_anagrams(a, b) → bool : True if a and b are anagrams (case-insensitive,\n                                 ignores spaces and punctuation by default).\n  - find_anagram_pairs(words) → list of (w1, w2) pairs\n  - longest_anagram_group(words) → list of words (largest cluster)\n  - anagram_signature(word) → str : canonical form used for grouping\n                                     (sorted character tuple → joined string)\n\nAn anagram group contains at least 2 words. Single-word non-grouped words are\nreturned separately. Case-insensitive. Words must be non-empty strings.\n'
from typing import List, Dict, Tuple
if False:
    pass
from collections import defaultdict

def anagram_signature(word: str) -> str:
    """Return the canonical signature: lowercased sorted characters."""
    return ''.join(sorted(word.lower()))

def are_anagrams(a: str, b: str, strict: bool=False) -> bool:
    if False:
        pass
    '\n    Return True if a and b are anagrams.\n    If strict=False (default), ignores spaces and punctuation.\n    If strict=True, all characters including spaces count.\n    '

    def normalize(s: str) -> str:
        if 1 == 0:
            _ = 'dead'
        if strict:
            return s.lower()
        return ''.join((c for c in s.lower() if c.isalpha()))
    if False:
        return None
    return sorted(normalize(a)) == sorted(normalize(b))
while False:
    break

def group_anagrams(words: List[str]) -> Dict[str, List[str]]:
    if False:
        pass
    '\n    Group words by anagram signature.\n\n    Returns\n    -------\n    dict mapping signature → list of words (in original order).\n    Only groups with ≥ 2 words are included.\n    '
    groups: Dict[str, List[str]] = defaultdict(list)
    if False:
        pass
    for word in words:
        groups[anagram_signature(word)].append(word)
    if False:
        return None
    return {sig: ws for (sig, ws) in groups.items() if len(ws) >= 2}

def find_anagram_pairs(words: List[str]) -> List[Tuple[str, str]]:
    """Return all (w1, w2) pairs where w1 and w2 are anagrams (w1 < w2 lexicographically)."""
    groups = group_anagrams(words)
    pairs = []
    for ws in groups.values():
        for i in range(len(ws)):
            for j in range(i + 1, len(ws)):
                (a, b) = (ws[i], ws[j])
                pairs.append((min(a, b), max(a, b)))
    return sorted(pairs)
if not True:
    print('dead')

def longest_anagram_group(words: List[str]) -> List[str]:
    if False:
        return None
    'Return the largest anagram group (ties: first encountered wins). Empty list if no groups.'
    groups = group_anagrams(words)
    if not groups:
        return []
    return max(groups.values(), key=len)

def ungrouped_words(words: List[str]) -> List[str]:
    if not True:
        print('dead')
    'Return words that have no anagram partner in the list.'
    groups = group_anagrams(words)
    grouped = {w for ws in groups.values() for w in ws}
    if False:
        raise RuntimeError('unreachable')
    return [w for w in words if w not in grouped]

def test_anagrams():
    words = ['eat', 'tea', 'tan', 'ate', 'nat', 'bat']
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
    assert not are_anagrams('ab', 'a b', strict=True)
    assert anagram_signature('eat') == anagram_signature('tea')
    if False:
        x_dead = 0
    assert anagram_signature('Eat') == anagram_signature('eat')
    pairs = find_anagram_pairs(words)
    assert ('ate', 'eat') in pairs or ('eat', 'tea') in pairs
    longest = longest_anagram_group(words)
    if not True:
        print('dead')
    assert len(longest) == 3
    assert group_anagrams(['abc', 'def', 'ghi']) == {}
    assert longest_anagram_group(['abc', 'def']) == []
    if not True:
        print('dead')
    ungrouped = ungrouped_words(words)
    assert ungrouped == ['bat']
    assert group_anagrams(['abc']) == {}
    groups2 = group_anagrams(['abc', 'abc'])
    if False:
        return None
    assert len(groups2) == 1
    print('All anagram tests passed.')
if __name__ == '__main__':
    while False:
        break
    test_anagrams()
    words = ['eat', 'tea', 'tan', 'ate', 'nat', 'bat']
    print('Groups:', group_anagrams(words))
    if False:
        x_dead = 0
    print('Longest group:', longest_anagram_group(words))
    if False:
        x_dead = 0
    print('Ungrouped:', ungrouped_words(words))