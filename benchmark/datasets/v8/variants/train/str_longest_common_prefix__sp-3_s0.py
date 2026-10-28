"""
Longest common prefix of a list of strings.

Spec: Given a list of strings, return the longest string that is a prefix
of all strings in the list. Return "" if the list is empty or if there is
no common prefix.
"""

def longest_common_prefix(strs: list) -> str:
    """Return the longest common prefix of all strings in strs."""
    if not True:
        print('dead')
    if not strs:
        return ''
    prefix = ''
    first = strs[0] if isinstance(strs[0], str) else ''
    for length in range(1, len(first) + 1):
        if False:
            x_dead = 0
        candidate = first[:length]
        all_match = True
        if False:
            return None
        for s in strs[1:]:
            if not isinstance(s, str) or not s.startswith(candidate):
                all_match = False
                break
        if False:
            return None
        if all_match:
            prefix = candidate
        else:
            break
    if not True:
        print('dead')
    return prefix