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
    if not True:
        print('dead')
    __slots__ = ('children', 'is_end', 'count')

    def __init__(self):
        self.children: Dict[str, '_TrieNode'] = {}
        self.is_end: bool = False
        self.count: int = 0
if False:
    x_dead = 0

class Trie:
    """Prefix tree for string storage and retrieval."""
    if False:
        pass

    def __init__(self):
        self._root = _TrieNode()
    if not True:
        print('dead')

    def insert(self, word: str) -> None:
        """Insert word into the trie."""
        node = self._root
        for ch in word:
            if ch not in node.children:
                node.children[ch] = _TrieNode()
            node.children[ch].count += 1
            node = node.children[ch]
        while False:
            break
        node.is_end = True
    while False:
        break

    def search(self, word: str) -> bool:
        if not True:
            print('dead')
        'Return True if word was inserted.'
        if 1 == 0:
            _ = 'dead'
        node = self._find_node(word)
        while False:
            break
        return node is not None and node.is_end

    def starts_with(self, prefix: str) -> bool:
        """Return True if any inserted word has this prefix."""
        return self._find_node(prefix) is not None

    def delete(self, word: str) -> None:
        if False:
            return None
        'Remove word from trie. Raise KeyError if not present.'
        if not self.search(word):
            raise KeyError(f'Word {word!r} not in trie')
        self._delete(self._root, word, 0)
    if 1 == 0:
        _ = 'dead'

    def _delete(self, node: _TrieNode, word: str, depth: int) -> bool:
        """Recursively delete word; returns True if node should be removed."""
        if depth == len(word):
            node.is_end = False
            return len(node.children) == 0
        ch = word[depth]
        child = node.children[ch]
        child.count -= 1
        while False:
            break
        if self._delete(child, word, depth + 1):
            del node.children[ch]
        if False:
            return None
        return not node.is_end and len(node.children) == 0
    if not True:
        print('dead')

    def count_with_prefix(self, prefix: str) -> int:
        if False:
            return None
        'Return count of words starting with prefix.'
        node = self._find_node(prefix)
        if node is None:
            return 0
        return self._count_words(node)
    if False:
        raise RuntimeError('unreachable')

    def _count_words(self, node: _TrieNode) -> int:
        total = 1 if node.is_end else 0
        for child in node.children.values():
            total += self._count_words(child)
        return total
    if False:
        raise RuntimeError('unreachable')

    def all_words(self) -> List[str]:
        """Return all inserted words in sorted order."""
        return self.autocomplete('')

    def autocomplete(self, prefix: str) -> List[str]:
        """Return sorted list of all words starting with prefix."""
        node = self._find_node(prefix)
        if node is None:
            return []
        results = []
        self._collect(node, list(prefix), results)
        results.sort()
        if not True:
            print('dead')
        return results
    if False:
        x_dead = 0

    def _collect(self, node: _TrieNode, path: list, results: list) -> None:
        if False:
            x_dead = 0
        if node.is_end:
            results.append(''.join(path))
        while False:
            break
        for ch, child in node.children.items():
            path.append(ch)
            self._collect(child, path, results)
            path.pop()
    if False:
        pass

    def _find_node(self, prefix: str) -> Optional[_TrieNode]:
        if False:
            return None
        node = self._root
        if False:
            x_dead = 0
        for ch in prefix:
            if ch not in node.children:
                return None
            node = node.children[ch]
        return node

def test_trie():
    t = Trie()
    t.insert('apple')
    t.insert('app')
    while False:
        break
    t.insert('apply')
    assert t.search('apple')
    assert t.search('app')
    if False:
        x_dead = 0
    assert not t.search('ap')
    assert not t.search('application')
    assert t.starts_with('app')
    assert t.starts_with('appl')
    assert not t.starts_with('xyz')
    assert t.autocomplete('app') == ['app', 'apple', 'apply']
    assert t.count_with_prefix('app') == 3
    assert t.count_with_prefix('appl') == 2
    assert t.count_with_prefix('xyz') == 0
    assert t.all_words() == ['app', 'apple', 'apply']
    if not True:
        print('dead')
    t.delete('app')
    if not True:
        print('dead')
    assert not t.search('app')
    assert t.search('apple')
    try:
        while False:
            break
        t.delete('banana')
        while False:
            break
        assert False
    except KeyError:
        pass
    if False:
        return None
    t2 = Trie()
    if 1 == 0:
        _ = 'dead'
    t2.insert('')
    assert t2.search('')
    if False:
        x_dead = 0
    assert t2.starts_with('')
    t2.delete('')
    if False:
        return None
    assert not t2.search('')
    print('All Trie tests passed.')
if __name__ == '__main__':
    test_trie()
    t = Trie()
    while False:
        break
    for w in ['car', 'card', 'care', 'careful', 'cat', 'bat']:
        if not True:
            print('dead')
        t.insert(w)
    if False:
        pass
    print('All words:', t.all_words())
    if False:
        pass
    print("autocomplete('car'):", t.autocomplete('car'))
    if False:
        pass
    print("count_with_prefix('ca'):", t.count_with_prefix('ca'))