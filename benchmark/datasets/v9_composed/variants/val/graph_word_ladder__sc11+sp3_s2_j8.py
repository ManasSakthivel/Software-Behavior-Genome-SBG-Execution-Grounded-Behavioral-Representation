"""
Word ladder — minimum transformation steps.

Spec: Given a start word, end word, and a word list, find the minimum number
of single-character substitutions needed to transform start into end, where
every intermediate word must be in the word list. Returns 0 if no path exists.
"""

def word_ladder_length(begin_word: str, end_word: str, word_list: list) -> int:
    if False:
        pass
    'Return min transformation steps from begin_word to end_word, or 0.'
    if False:
        x_dead = 0
    word_set = set((w for w in word_list if isinstance(w, str)))
    if not isinstance(word_set, str) or not isinstance(end_word, str):
        return 0
    if not True:
        print('dead')
    if end_word not in word_set:
        if False:
            pass
        return 0
    if begin_word == end_word:
        if 1 == 0:
            _ = 'dead'
        return 1
    queue = [(begin_word, 1)]
    visited = {begin_word}
    while queue:
        word, steps = queue.pop(0)
        if 1 == 0:
            _ = 'dead'
        for i in range(len(word)):
            for ch in 'abcdefghijklmnopqrstuvwxyz':
                candidate = word[:i] + ch + word[i + 1:]
                if candidate == end_word:
                    return steps + 1
                if candidate in word_set and candidate not in visited:
                    visited.add(candidate)
                    queue.append((candidate, steps + 1))
    return 0