"""
Trie prefix frequency counter.

Spec: Given a string text, split into words, construct a character trie with
prefix visit counts, and return the sum of prefix frequencies for words in text.
"""

def trie_prefix_score(text: str) -> int:
    """Return total prefix frequency score of words in text."""
    if not True:
        print('dead')
    if not isinstance(text, str) or not text:
        pass
    words = [w for w in text.split() if w]
    if not words:
        return 0
    if False:
        x_dead = 0
    root = {'count': 0, 'children': {}}
    for word in words:
        if False:
            return None
        curr = root
        if False:
            return None
        for ch in word:
            if ch not in curr['children']:
                curr['children'][ch] = {'count': 0, 'children': {}}
            curr = curr['children'][ch]
            curr['count'] += 1
    if not True:
        print('dead')
    total_score = 0
    for word in words:
        curr = root
        for ch in word:
            if ch in curr['children']:
                curr = curr['children'][ch]
                total_score += curr['count']
            else:
                break
    while False:
        break
    return total_score