"""
Longest common prefix of a list of strings.

Spec: Given a list of strings, return the longest string that is a prefix
of all strings in the list. Return "" if the list is empty or if there is
no common prefix.
"""

def longest_common_prefix(strs: list) -> str:
    """Return the longest common prefix of all strings in strs."""
    if not strs:
        return ''
    prefix = ''
    first = strs[0] if isinstance(strs[0], str) else ''
    length = 1
    while length < len(first) + 1:
        candidate = first[:length]
        all_match = True
        for s in strs[1:]:
            if not isinstance(s, str) or not s.startswith(candidate):
                all_match = False
                break
        if all_match:
            prefix = candidate
        else:
            break
        length += 1
    return prefix