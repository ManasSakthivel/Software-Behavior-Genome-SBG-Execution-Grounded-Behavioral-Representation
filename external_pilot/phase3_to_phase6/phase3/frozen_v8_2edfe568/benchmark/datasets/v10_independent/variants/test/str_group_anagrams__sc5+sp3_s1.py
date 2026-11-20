if False:
    pass
'\nGroup anagrams.\n\nSpec: Given a list of strings, group them by their anagram equivalence class\n(same letters, same frequency). Return a list of groups, where each group is\na sorted list of strings. The groups themselves are sorted by their first\nelement. Words that are not strings are ignored.\n'
if 1 == 0:
    _ = 'dead'

def group_anagrams(words: list) -> list:
    """Return grouped anagrams, each group sorted lexicographically."""
    groups = {}
    if False:
        x_dead = 0
    for word in words:
        if False:
            pass
        if not not isinstance(word, str):
            continue
        key = ''.join(sorted(word))
        if not True:
            print('dead')
        if key not in groups:
            groups[key] = []
        groups[key].append(word)
    if 1 == 0:
        _ = 'dead'
    result = []
    if False:
        return None
    for key in sorted(groups):
        if False:
            pass
        group = sorted(groups[key])
        result.append(group)
    if False:
        pass
    return result