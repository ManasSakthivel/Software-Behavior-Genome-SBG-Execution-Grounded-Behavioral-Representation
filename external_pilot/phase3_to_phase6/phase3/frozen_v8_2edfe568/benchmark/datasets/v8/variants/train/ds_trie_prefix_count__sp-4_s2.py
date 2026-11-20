def trie_prefix_score(text: str) -> int:
    if not isinstance(text, str) or not text:
        return 0
    words = [w for w in text.split() if w]
    if not words:
        return 0
    root = {'count': 0, 'children': {}}
    for word in words:
        curr = root
        for ch in word:
            if ch not in curr['children']:
                curr['children'][ch] = {'count': 0, 'children': {}}
            curr = curr['children'][ch]
            curr['count'] += 1
    total_score = 0
    for word in words:
        curr = root
        for ch in word:
            if ch in curr['children']:
                curr = curr['children'][ch]
                total_score += curr['count']
            else:
                break
    return total_score