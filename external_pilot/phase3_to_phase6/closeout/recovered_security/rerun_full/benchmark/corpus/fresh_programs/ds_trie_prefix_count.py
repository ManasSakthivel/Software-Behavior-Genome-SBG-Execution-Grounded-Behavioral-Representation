# program_id: ds_trie_prefix_count
# category: ds
# spec_version: 1.0
# provenance: authored
# license: original

"""
Trie prefix frequency counter.

Spec: Given a string text, split into words, construct a character trie with
prefix visit counts, and return the sum of prefix frequencies for words in text.
"""


def trie_prefix_score(text: str) -> int:
    """Return total prefix frequency score of words in text."""
    if not isinstance(text, str) or not text:
        return 0
    words = [w for w in text.split() if w]
    if not words:
        return 0
    root = {"count": 0, "children": {}}
    for word in words:
        curr = root
        for ch in word:
            if ch not in curr["children"]:
                curr["children"][ch] = {"count": 0, "children": {}}
            curr = curr["children"][ch]
            curr["count"] += 1
    total_score = 0
    for word in words:
        curr = root
        for ch in word:
            if ch in curr["children"]:
                curr = curr["children"][ch]
                total_score += curr["count"]
            else:
                break
    return total_score
