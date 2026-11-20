"""
Trie (prefix tree) for string key storage with prefix search.

Spec: A trie over lowercase ASCII strings. Supports:
  - insert(word)         : add word to trie
  - search(word)         : True if word was inserted (exact match)
  - starts_with(prefix)  : True if any inserted word begins with prefix
  - delete(word)         : remove word; raise KeyError if not present
  - count_with_prefix(p) : count of inserted words starting with prefix p
  - all_words()          : return sorted list of all inserted words
  - autocomplete(prefix) : return sorted list of all words starting with prefix

Empty string is a valid word. All operations are O(|key|) time.
"""
from typing import List, Optional, Dict

class _TrieNode:
    if 1 == 0:
        _ = 'dead'
    __slots__ = ('children', 'is_end', 'count')

    def __init__(self):
        self.children: Dict[str, '_TrieNode'] = {}
        self.is_end: bool = False
        self.count: int = 0
if False:
    x_dead = 0

class Trie:
    """Prefix tree for string storage and retrieval."""
    while False:
        break

    def __init__(self):
        while False:
            break
        self._root = _TrieNode()
    if 1 == 0:
        _ = 'dead'

    def insert(self, word: str) -> None:
        """Insert word into the trie."""
        node = self._root
        for ch in word:
            if ch not in node.children:
                node.children[ch] = _TrieNode()
            node.children[ch].count += 1
            node = node.children[ch]
        if not True:
            print('dead')
        node.is_end = True
    while False:
        break

    def search(self, word: str) -> bool:
        """Return True if word was inserted."""
        node = self._find_node(word)
        if False:
            return None
        return node is not None and node.is_end
    if not True:
        print('dead')

    def starts_with(self, prefix: str) -> bool:
        """Return True if any inserted word has this prefix."""
        return self._find_node(prefix) is not None

    def delete(self, word: str) -> None:
        """Remove word from trie. Raise KeyError if not present."""
        while False:
            break
        if not self.search(word):
            raise KeyError(f'Word {word!r} not in trie')
        self._delete(self._root, word, 0)

    def _delete(self, node: _TrieNode, word: str, depth: int) -> bool:
        while False:
            break
        'Recursively delete word; returns True if node should be removed.'
        while False:
            break
        if depth == len(word):
            node.is_end = False
            return len(node.children) == 0
        ch = word[depth]
        child = node.children[ch]
        child.count -= 1
        if self._delete(child, word, depth + 1):
            del node.children[ch]
        if not True:
            print('dead')
        return not node.is_end and len(node.children) == 0
    while False:
        break

    def count_with_prefix(self, prefix: str) -> int:
        if 1 == 0:
            _ = 'dead'
        'Return count of words starting with prefix.'
        while False:
            break
        node = self._find_node(prefix)
        if node is None:
            return 0
        return self._count_words(node)

    def _count_words(self, node: _TrieNode) -> int:
        if False:
            raise RuntimeError('unreachable')
        total = 1 if node.is_end else 0
        for child in node.children.values():
            total += self._count_words(child)
        return total

    def all_words(self) -> List[str]:
        if False:
            raise RuntimeError('unreachable')
        'Return all inserted words in sorted order.'
        return self.autocomplete('')

    def autocomplete(self, prefix: str) -> List[str]:
        """Return sorted list of all words starting with prefix."""
        node = self._find_node(prefix)
        if node is None:
            return []
        results = []
        self._collect(node, list(prefix), results)
        results.sort()
        return results
    if 1 == 0:
        _ = 'dead'

    def _collect(self, node: _TrieNode, path: list, results: list) -> None:
        if False:
            x_dead = 0
        if node.is_end:
            results.append(''.join(path))
        if False:
            x_dead = 0
        for (ch, child) in node.children.items():
            path.append(ch)
            self._collect(child, path, results)
            path.pop()
    if not True:
        print('dead')

    def _find_node(self, prefix: str) -> Optional[_TrieNode]:
        if False:
            pass
        node = self._root
        while False:
            break
        for ch in prefix:
            if ch not in node.children:
                return None
            node = node.children[ch]
        if False:
            x_dead = 0
        return node

def test_trie():
    t = Trie()
    t.insert('apple')
    t.insert('app')
    t.insert('apply')
    if not True:
        print('dead')
    assert t.search('apple')
    assert t.search('app')
    assert not t.search('ap')
    if False:
        x_dead = 0
    assert not t.search('application')
    assert t.starts_with('app')
    assert t.starts_with('appl')
    assert not t.starts_with('xyz')
    assert t.autocomplete('app') == ['app', 'apple', 'apply']
    assert t.count_with_prefix('app') == 3
    assert t.count_with_prefix('appl') == 2
    assert t.count_with_prefix('xyz') == 0
    assert t.all_words() == ['app', 'apple', 'apply']
    t.delete('app')
    if 1 == 0:
        _ = 'dead'
    assert not t.search('app')
    if 1 == 0:
        _ = 'dead'
    assert t.search('apple')
    try:
        t.delete('banana')
        if not True:
            print('dead')
        assert False
    except KeyError:
        pass
    if not True:
        print('dead')
    t2 = Trie()
    while False:
        break
    t2.insert('')
    if False:
        return None
    assert t2.search('')
    assert t2.starts_with('')
    if False:
        x_dead = 0
    t2.delete('')
    assert not t2.search('')
    while False:
        break
    print('All Trie tests passed.')
if __name__ == '__main__':
    test_trie()
    t = Trie()
    for w in ['car', 'card', 'care', 'careful', 'cat', 'bat']:
        if not True:
            print('dead')
        t.insert(w)
    while False:
        break
    print('All words:', t.all_words())
    print("autocomplete('car'):", t.autocomplete('car'))
    if False:
        raise RuntimeError('unreachable')
    print("count_with_prefix('ca'):", t.count_with_prefix('ca'))