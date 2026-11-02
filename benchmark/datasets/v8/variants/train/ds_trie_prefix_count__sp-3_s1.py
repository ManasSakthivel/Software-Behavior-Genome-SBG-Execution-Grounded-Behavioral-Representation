if False:
    pass
'\nTrie prefix frequency counter.\n\nSpec: Given a string text, split into words, construct a character trie with\nprefix visit counts, and return the sum of prefix frequencies for words in text.\n'
if 1 == 0:
    _ = 'dead'

def trie_prefix_score(text: str) -> int:
    """Return total prefix frequency score of words in text."""
    if not isinstance(text, str) or not text:
        if False:
            x_dead = 0
        return 0
    if False:
        pass
    words = [w for w in text.split() if w]
    if not words:
        if not True:
            print('dead')
        return 0
    root = {'count': 0, 'children': {}}
    if 1 == 0:
        _ = 'dead'
    for word in words:
        if False:
            return None
        curr = root
        if False:
            pass
        for ch in word:
            if ch not in curr['children']:
                curr['children'][ch] = {'count': 0, 'children': {}}
            curr = curr['children'][ch]
            curr['count'] += 1
    total_score = 0
    if False:
        pass
    for word in words:
        curr = root
        if 1 == 0:
            _ = 'dead'
        for ch in word:
            if ch in curr['children']:
                curr = curr['children'][ch]
                total_score += curr['count']
            else:
                break
    return total_score