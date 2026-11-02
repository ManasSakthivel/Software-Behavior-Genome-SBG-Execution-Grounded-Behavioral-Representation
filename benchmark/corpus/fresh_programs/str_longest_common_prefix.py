# program_id: str_longest_common_prefix
# category: str
# spec_version: 1.0
# provenance: authored
# license: original

"""
Longest common prefix of a list of strings.

Spec: Given a list of strings, return the longest string that is a prefix
of all strings in the list. Return "" if the list is empty or if there is
no common prefix.
"""


def longest_common_prefix(strs: list) -> str:
    """Return the longest common prefix of all strings in strs."""
    if not strs:
        return ""
    prefix = ""
    first = strs[0] if isinstance(strs[0], str) else ""
    for length in range(1, len(first) + 1):
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
    return prefix
