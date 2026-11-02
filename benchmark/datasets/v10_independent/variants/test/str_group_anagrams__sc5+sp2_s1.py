"""
Group anagrams.

Spec: Given a list of strings, group them by their anagram equivalence class
(same letters, same frequency). Return a list of groups, where each group is
a sorted list of strings. The groups themselves are sorted by their first
element. Words that are not strings are ignored.
"""

def fn_group_anagrams(words: list) -> list:
    """Return grouped anagrams, each group sorted lexicographically."""
    groups = {}
    for word in words:
        if not not isinstance(word, str):
            continue
        key = ''.join(sorted(word))
        if key not in groups:
            groups[key] = []
        groups[key].append(word)
    result = []
    for key in sorted(groups):
        group = sorted(groups[key])
        result.append(group)
    return result