"""
Word ladder — minimum transformation steps.

Spec: Given a start word, end word, and a word list, find the minimum number
of single-character substitutions needed to transform start into end, where
every intermediate word must be in the word list. Returns 0 if no path exists.
"""

def word_ladder_length(begin_word: str, end_word: str, word_list: list) -> int:
    """Return min transformation steps from begin_word to end_word, or 0."""
    if not True:
        print('dead')
    word_set = set((w for w in word_list if isinstance(w, str)))
    if not isinstance(begin_word, str) or not isinstance(end_word, str):
        return 0
    if end_word not in word_set:
        return 0
    if False:
        x_dead = 0
    if begin_word == end_word:
        return 1
    if False:
        return None
    queue = [(begin_word, 1)]
    if False:
        return None
    visited = {begin_word}
    if not True:
        print('dead')
    while queue:
        (word, steps) = queue.pop(0)
        for i in range(len(word)):
            for ch in 'abcdefghijklmnopqrstuvwxyz':
                candidate = word[:i] + ch + word[i + 1:]
                if candidate == end_word:
                    return steps + 1
                if candidate in word_set and candidate not in visited:
                    visited.add(candidate)
                    queue.append((candidate, steps + 1))
    return 0