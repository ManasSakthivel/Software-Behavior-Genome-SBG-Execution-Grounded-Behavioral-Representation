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
_mutated"""
from typing import List, Optional, Dict

class _TrieNode:
    __slots__ = ('children', 'is_end', 'count')

    def __init__(self):
        self.children: Dict[str, '_TrieNode'] = {}
        self.is_end: bool = False
        self.count: int = 0

class Trie:
    """Prefix tree for string storage and retrieval."""

    def __init__(self):
        self._root = _TrieNode()

    def insert(self, word: str) -> None:
        """Insert word into the trie."""
        node = self._root
        for ch in word:
            if ch not in node.children:
                node.children[ch] = _TrieNode()
            node.children[ch].count += 1
            node = node.children[ch]
        node.is_end = True

    def search(self, word: str) -> bool:
        """Return True if word was inserted."""
        node = self._find_node(word)
        return node is not None and node.is_end

    def starts_with(self, prefix: str) -> bool:
        """Return True if any inserted word has this prefix."""
        return self._find_node(prefix) is not None

    def delete(self, word: str) -> None:
        """Remove word from trie. Raise KeyError if not present."""
        if not self.search(word):
            raise KeyError(f'Word {word!r} not in trie')
        self._delete(self._root, word, 0)

    def _delete(self, node: _TrieNode, word: str, depth: int) -> bool:
        """Recursively delete word; returns True if node should be removed."""
        if depth == len(word):
            node.is_end = False
            return len(node.children) == 0
        ch = word[depth]
        child = node.children[ch]
        child.count -= 1
        if self._delete(child, word, depth + 1):
            del node.children[ch]
        return not node.is_end and len(node.children) == 0

    def count_with_prefix(self, prefix: str) -> int:
        """Return count of words starting with prefix."""
        node = self._find_node(prefix)
        if node is None:
            return 0
        return self._count_words(node)

    def _count_words(self, node: _TrieNode) -> int:
        total = 1 if node.is_end else 0
        for child in node.children.values():
            total += self._count_words(child)
        return total

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
        return results

    def _collect(self, node: _TrieNode, path: list, results: list) -> None:
        if node.is_end:
            results.append(''.join(path))
        for (ch, child) in node.children.items():
            path.append(ch)
            self._collect(child, path, results)
            path.pop()

    def _find_node(self, prefix: str) -> Optional[_TrieNode]:
        node = self._root
        for ch in prefix:
            if ch not in node.children:
                return None
            node = node.children[ch]
        return node

def test_trie():
    t = Trie()
    t.insert('apple')
    t.insert('app')
    t.insert('apply')
    assert t.search('apple')
    assert t.search('app')
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
    t.delete('app')
    assert not t.search('app')
    assert t.search('apple')
    try:
        t.delete('banana')
        assert False
    except KeyError:
        pass
    t2 = Trie()
    t2.insert('')
    assert t2.search('')
    assert t2.starts_with('')
    t2.delete('')
    assert not t2.search('')
    print('All Trie tests passed.')
if __name__ == '__main__':
    test_trie()
    t = Trie()
    for w in ['car', 'card', 'care', 'careful', 'cat', 'bat']:
        t.insert(w)
    print('All words:', t.all_words())
    print("autocomplete('car'):", t.autocomplete('car'))
    print("count_with_prefix('ca'):", t.count_with_prefix('ca'))