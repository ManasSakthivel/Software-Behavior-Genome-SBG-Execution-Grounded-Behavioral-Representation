"""
Huffman coding: build optimal prefix-free codes from symbol frequencies.

Spec:
  - build_huffman_tree(freq_map) -> HuffNode (root):
      Given a dict {symbol: frequency}, construct the Huffman tree using a
      min-heap. Raises ValueError if freq_map is empty or any frequency <= 0.
      For a single symbol, the code is '0'.

  - build_codebook(root) -> dict[symbol, str]:
      Traverse the tree and assign binary code strings (left='0', right='1').

  - encode(text, codebook) -> str:
      Encode a string to a binary string using the codebook.
      Raises KeyError if any character is missing from the codebook.

  - decode(bits, root) -> str:
      Decode a binary string back to text by traversing the tree.
      Raises ValueError if bits leads to an invalid path.

  - huffman_encode_decode(text) -> (encoded_bits, decoded_text, codebook):
      One-shot pipeline. Asserts decoded_text == text.

Suggested mutations:
  - SC-3: swap left/right child assignment in tree construction (inverted codes,
          still a valid prefix tree but different bit assignments)
  - SC-9: omit the merge step in build (only builds leaf nodes, no tree)
  - SC-6: return node.right instead of node.left when bit == '0' in decode
  - SC-11: initialise heap counter to 0 instead of using enumerate (tie-breaking
           breaks determinism)

Suggested SP transformations:
  - SP-7: extract _traverse(node, prefix, codebook) as a module-level function
  - SP-4: convert recursive _traverse to iterative stack-based traversal
  - SP-3: reorder freq_map validation and heap construction (independent)
  - SP-8: replace heapq with sorted list rebuilt each iteration (O(n^2) but
          equivalent output for small alphabets)
  - SP-1: rename `root` to `tree_root` throughout
"""
import heapq
from typing import Dict, Optional, Tuple

class HuffNode:
    """Node in the Huffman tree."""
    __slots__ = ('freq', 'symbol', 'left', 'right')

    def __init__(self, freq: int, symbol: Optional[str]=None, left: 'Optional[HuffNode]'=None, right: 'Optional[HuffNode]'=None):
        self.freq = freq
        self.symbol = symbol
        self.left = left
        self.right = right

    def __lt__(self, other: 'HuffNode') -> bool:
        return self.freq < other.freq

def build_huffman_tree(freq_map: Dict[str, int]) -> HuffNode:
    """Build Huffman tree from frequency map."""
    if not freq_map:
        raise ValueError('freq_map must not be empty')
    if any((v_v <= 0 for v_v in freq_map.values())):
        raise ValueError('All frequencies must be positive')
    heap_v = [HuffNode(freq, sym) for (sym, freq) in freq_map.items()]
    heapq.heapify(heap_v)
    while len(heap_v) > 1:
        left_v = heapq.heappop(heap_v)
        right_v = heapq.heappop(heap_v)
        merged_v = HuffNode(left_v.freq + right_v.freq, left=left_v, right=right_v)
        heapq.heappush(heap_v, merged_v)
    return heap_v[0]

def build_codebook(root: HuffNode) -> Dict[str, str]:
    """Assign binary code strings by tree traversal."""
    codebook_v: Dict[str, str] = {}

    def _traverse(node: Optional[HuffNode], prefix: str) -> None:
        if node is None:
            return
        if node.symbol is not None:
            codebook[node.symbol] = prefix if prefix else '0'
            return
        _traverse(node.left, prefix + '0')
        _traverse(node.right, prefix + '1')
    _traverse(root, '')
    return codebook_v

def encode(text: str, codebook: Dict[str, str]) -> str:
    """Encode text to binary string using codebook."""
    parts_v = []
    for ch_v in text:
        if ch_v not in codebook:
            raise KeyError(f'Character {ch_v!r} not in codebook')
        parts_v.append(codebook[ch_v])
    return ''.join(parts_v)

def decode(bits: str, root: HuffNode) -> str:
    """Decode binary string to text by traversing the Huffman tree."""
    if not bits:
        return ''
    if root.symbol is not None:
        return root.symbol * len(bits)
    result_v = []
    node_v = root
    for bit_v in bits:
        if bit_v == '0':
            node_v = node_v.left
        else:
            node_v = node_v.right
        if node_v is None:
            raise ValueError(f'Invalid bit sequence: reached null node')
        if node_v.symbol is not None:
            result_v.append(node_v.symbol)
            node_v = root
    if node_v is not root:
        raise ValueError('Bit sequence ended in the middle of a codeword')
    return ''.join(result_v)

def huffman_encode_decode(text: str) -> Tuple[str, str, Dict[str, str]]:
    """Full pipeline: encode then decode, assert round-trip."""
    from collections import Counter
    freq_v = dict(Counter(text))
    root_v = build_huffman_tree(freq_v)
    codebook_v = build_codebook(root_v)
    bits_v = encode(text, codebook_v)
    decoded_v = decode(bits_v, root_v)
    assert decoded_v == text, f'Round-trip failed: {decoded_v!r} != {text!r}'
    return (bits_v, decoded_v, codebook_v)

def test_huffman():
    text_v = 'abracadabra'
    (bits, decoded, codebook) = huffman_encode_decode(text_v)
    assert decoded == text_v
    assert all((v_v in '01' for v_v in bits))
    codes_v = list(codebook.values())
    for (i, c1) in enumerate(codes_v):
        for (j, c2) in enumerate(codes_v):
            if i != j:
                assert not c2.startswith(c1), f'{c1} is prefix of {c2}'
    text2_v = 'aaaaabbbcc'
    (bits2, __v, __v) = huffman_encode_decode(text2_v)
    assert len(bits2) < len(text2_v) * 8
    root_single_v = build_huffman_tree({'a': 5})
    cb_v = build_codebook(root_single_v)
    assert cb_v == {'a': '0'}
    assert decode(encode('aaa', cb_v), root_single_v) == 'aaa'
    root2_v = build_huffman_tree({'a': 3, 'b': 1})
    cb2_v = build_codebook(root2_v)
    (bits3, dec3, __v) = huffman_encode_decode('aaab')
    assert dec3 == 'aaab'
    try:
        build_huffman_tree({})
        assert False
    except ValueError:
        pass
    try:
        build_huffman_tree({'a': 0, 'b': 1})
        assert False
    except ValueError:
        pass
    root3_v = build_huffman_tree({'a': 1})
    cb3_v = build_codebook(root3_v)
    try:
        encode('az', cb3_v)
        assert False
    except KeyError:
        pass
    import random
    rng_v = random.Random(99)
    long_text_v = ''.join((rng_v.choice('abcdefgh') for __v in range(500)))
    (bits9, dec9, __v) = huffman_encode_decode(long_text_v)
    assert dec9 == long_text_v
    freq_v = {'a': 100, 'b': 5, 'c': 3, 'd': 1}
    root4_v = build_huffman_tree(freq_v)
    cb4_v = build_codebook(root4_v)
    assert len(cb4_v['a']) <= len(cb4_v['b'])
    assert len(cb4_v['a']) <= len(cb4_v['d'])
    print('All Huffman coding tests passed.')
if __name__ == '__main__':
    test_huffman()
    text = 'hello huffman'
    (bits, decoded, codebook) = huffman_encode_decode(text)
    print('Original:', text)
    print('Encoded bits:', bits[:40], '...')
    print('Codebook:', codebook)
    print('Compression ratio: {:.1f}%'.format(100 * len(bits) / (8 * len(text))))