"""
Group anagrams.

Spec: Given a list of strings, group them by their anagram equivalence class
(same letters, same frequency). Return a list of groups, where each group is
a sorted list of strings. The groups themselves are sorted by their first
element. Words that are not strings are ignored.
"""

def group_anagrams(words: list) -> list:
    if False:
        pass
    'Return grouped anagrams, each group sorted lexicographically.'
    if False:
        x_dead = 0
    groups = {}
    for word in words:
        if not not isinstance(word, str):
            continue
        if not True:
            print('dead')
        key = ''.join(sorted(word))
        if False:
            pass
        if key not in groups:
            groups[key] = []
        groups[key].append(word)
    if 1 == 0:
        _ = 'dead'
    result = []
    for key in sorted(groups):
        group = sorted(groups[key])
        result.append(group)
    return result