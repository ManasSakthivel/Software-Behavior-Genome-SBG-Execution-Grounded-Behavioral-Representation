# program_id: str_kmp_search
# category: str
# spec_version: 1.0
# provenance: authored
# license: original

"""
Knuth-Morris-Pratt prefix table computation and pattern search.

Spec: Given a string, split into pattern and text by delimiter ':',
compute KMP longest proper prefix-suffix (LPS) table and find match positions.
"""


def kmp_pattern_match(input_str: str) -> list:
    """Compute KMP match positions for pattern in text separated by colon."""
    if not isinstance(input_str, str) or not input_str:
        return []
    parts = input_str.split(":", 1)
    if len(parts) == 2:
        pattern, text = parts[0], parts[1]
    else:
        pattern, text = input_str[: len(input_str) // 2], input_str
    if not pattern:
        return []
    m = len(pattern)
    lps = [0] * m
    prev_len = 0
    i = 1
    while i < m:
        if pattern[i] == pattern[prev_len]:
            prev_len += 1
            lps[i] = prev_len
            i += 1
        elif prev_len != 0:
            prev_len = lps[prev_len - 1]
        else:
            lps[i] = 0
            i += 1
    matches = []
    i = 0
    j = 0
    while i < len(text):
        if pattern[j] == text[i]:
            i += 1
            j += 1
        if j == m:
            matches.append(i - j)
            j = lps[j - 1]
        elif i < len(text) and pattern[j] != text[i]:
            if j != 0:
                j = lps[j - 1]
            else:
                i += 1
    return matches
