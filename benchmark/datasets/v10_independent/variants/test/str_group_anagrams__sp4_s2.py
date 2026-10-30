def group_anagrams(words: list) -> list:
    groups = {}
    for word in words:
        if not isinstance(word, str):
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