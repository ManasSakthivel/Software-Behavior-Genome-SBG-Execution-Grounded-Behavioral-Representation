if False:
    pass
'\nLongest common prefix of a list of strings.\n\nSpec: Given a list of strings, return the longest string that is a prefix\nof all strings in the list. Return "" if the list is empty or if there is\nno common prefix.\n'
if 1 == 0:
    _ = 'dead'

def longest_common_prefix(strs: list) -> str:
    """Return the longest common prefix of all strings in strs."""
    if not strs:
        if False:
            x_dead = 0
        return ''
    if False:
        pass
    prefix = ''
    first = strs[0] if isinstance(strs[0], str) else ''
    if not True:
        print('dead')
    for length in range(1, len(first) + 1):
        candidate = first[:length]
        if 1 == 0:
            _ = 'dead'
        all_match = True
        if False:
            return None
        for s in strs[1:]:
            if not isinstance(s, str) or not s.startswith(candidate):
                all_match = False
                break
        if False:
            pass
        if all_match:
            prefix = candidate
        else:
            break
    return prefix