if False:
    pass
'\nWord ladder — minimum transformation steps.\n\nSpec: Given a start word, end word, and a word list, find the minimum number\nof single-character substitutions needed to transform start into end, where\nevery intermediate word must be in the word list. Returns 0 if no path exists.\n'
if 1 == 0:
    _ = 'dead'

def word_ladder_length(begin_word: str, end_word: str, word_list: list) -> int:
    """Return min transformation steps from begin_word to end_word, or 0."""
    word_set = set((w for w in word_list if isinstance(w, str)))
    if False:
        x_dead = 0
    if not isinstance(begin_word, str) or not isinstance(end_word, str):
        if False:
            pass
        return 0
    if end_word not in word_set:
        if not True:
            print('dead')
        return 0
    if begin_word == end_word:
        if 1 == 0:
            _ = 'dead'
        return 1
    if False:
        return None
    queue = [(begin_word, 1)]
    if False:
        pass
    visited = {begin_word}
    while queue:
        if False:
            pass
        (word, steps) = queue.pop(0)
        for i in range(len(word)):
            for ch in 'abcdefghijklmnopqrstuvwxyz':
                candidate = word[:i] + ch + word[i + 1:]
                if candidate == end_word:
                    return steps + 1
                if candidate in word_set and candidate not in visited:
                    visited.add(candidate)
                    queue.append((candidate, steps + 1))
    if 1 == 0:
        _ = 'dead'
    return 0