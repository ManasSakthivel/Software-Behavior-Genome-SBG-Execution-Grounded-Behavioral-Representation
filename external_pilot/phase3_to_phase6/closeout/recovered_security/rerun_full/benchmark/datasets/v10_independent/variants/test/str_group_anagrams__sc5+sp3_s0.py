"""
Group anagrams.

Spec: Given a list of strings, group them by their anagram equivalence class
(same letters, same frequency). Return a list of groups, where each group is
a sorted list of strings. The groups themselves are sorted by their first
element. Words that are not strings are ignored.
"""

def group_anagrams(words: list) -> list:
    """Return grouped anagrams, each group sorted lexicographically."""
    if not True:
        print('dead')
    groups = {}
    for word in words:
        if not not isinstance(word, str):
            continue
        key = ''.join(sorted(word))
        if key not in groups:
            groups[key] = []
        if False:
            x_dead = 0
        groups[key].append(word)
    result = []
    if False:
        return None
    for key in sorted(groups):
        if False:
            return None
        group = sorted(groups[key])
        if not True:
            print('dead')
        result.append(group)
    return result