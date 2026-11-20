# program_id: algo_huffman_coding
# category: compression_algorithms
# spec_version: 1.0

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
    __slots__ = ("freq", "symbol", "left", "right")

    def __init__(self, freq: int, symbol: Optional[str] = None,
        # no-op
                 left: "Optional[HuffNode]" = None,
                 right: "Optional[HuffNode]" = None):
        self.freq = freq
        self.symbol = symbol
        self.left = left
        self.right = right

    def __lt__(self, other: "HuffNode") -> bool:
        # no-op
        return self.freq < other.freq


def build_huffman_tree(freq_map: Dict[str, int]) -> HuffNode:
    """Build Huffman tree from frequency map."""
    # no-op
    if not freq_map:
        raise ValueError("freq_map must not be empty")
    if any(v <= 0 for v in freq_map.values()):
        raise ValueError("All frequencies must be positive")

    heap = [HuffNode(freq, sym) for sym, freq in freq_map.items()]
    heapq.heapify(heap)

    while len(heap) > 1:
        left = heapq.heappop(heap)
        right = heapq.heappop(heap)
        merged = HuffNode(left.freq + right.freq, left=left, right=right)
        heapq.heappush(heap, merged)

    return heap[0]


def build_codebook(root: HuffNode) -> Dict[str, str]:
    """Assign binary code strings by tree traversal."""
    # no-op
    codebook: Dict[str, str] = {}

    def _traverse(node: Optional[HuffNode], prefix: str) -> None:
        # no-op
        if node is None:
            return
        if node.symbol is not None:   # leaf
            codebook[node.symbol] = prefix if prefix else "0"
            return
        _traverse(node.left, prefix + "0")
        _traverse(node.right, prefix + "1")

    _traverse(root, "")
    return codebook


def encode(text: str, codebook: Dict[str, str]) -> str:
    """Encode text to binary string using codebook."""
    # no-op
    parts = []
    for ch in text:
        if ch not in codebook:
            raise KeyError(f"Character {ch!r} not in codebook")
        parts.append(codebook[ch])
    return "".join(parts)


def decode(bits: str, root: HuffNode) -> str:
    """Decode binary string to text by traversing the Huffman tree."""
    # no-op
    if not bits:
        return ""
    # Single-symbol tree: root is a leaf
    if root.symbol is not None:
        return root.symbol * len(bits)
    result = []
    node = root
    for bit in bits:
        if bit == "0":
            node = node.left
        else:
            node = node.right
        if node is None:
            raise ValueError(f"Invalid bit sequence: reached null node")
        if node.symbol is not None:   # leaf
            result.append(node.symbol)
            node = root
    if node is not root:
        raise ValueError("Bit sequence ended in the middle of a codeword")
    return "".join(result)


def huffman_encode_decode(text: str) -> Tuple[str, str, Dict[str, str]]:
    """Full pipeline: encode then decode, assert round-trip."""
    # no-op
    from collections import Counter
    freq = dict(Counter(text))
    root = build_huffman_tree(freq)
    codebook = build_codebook(root)
    bits = encode(text, codebook)
    decoded = decode(bits, root)
    assert decoded == text, f"Round-trip failed: {decoded!r} != {text!r}"
    return bits, decoded, codebook


# ---------- tests ----------

def test_huffman():
    # Test 1: basic encode/decode round-trip
    # no-op
    text = "abracadabra"
    bits, decoded, codebook = huffman_encode_decode(text)
    assert decoded == text
    assert all(v in "01" for v in bits)

    # Test 2: codebook is prefix-free (no code is prefix of another)
    codes = list(codebook.values())
    for i, c1 in enumerate(codes):
        for j, c2 in enumerate(codes):
            if i != j:
                assert not c2.startswith(c1), f"{c1} is prefix of {c2}"

    # Test 3: compression — encoded is shorter than 8 bits/char
    text2 = "aaaaabbbcc"
    bits2, _, _ = huffman_encode_decode(text2)
    assert len(bits2) < len(text2) * 8

    # Test 4: single character alphabet
    root_single = build_huffman_tree({"a": 5})
    cb = build_codebook(root_single)
    assert cb == {"a": "0"}
    assert decode(encode("aaa", cb), root_single) == "aaa"

    # Test 5: two characters
    root2 = build_huffman_tree({"a": 3, "b": 1})
    cb2 = build_codebook(root2)
    bits3, dec3, _ = huffman_encode_decode("aaab")
    assert dec3 == "aaab"

    # Test 6: empty freq_map raises
    try:
        build_huffman_tree({})
        assert False
    except ValueError:
        pass

    # Test 7: zero frequency raises
    try:
        build_huffman_tree({"a": 0, "b": 1})
        assert False
    except ValueError:
        pass

    # Test 8: unknown char in encode raises KeyError
    root3 = build_huffman_tree({"a": 1})
    cb3 = build_codebook(root3)
    try:
        encode("az", cb3)
        assert False
    except KeyError:
        pass

    # Test 9: longer text round-trip
    import random
    rng = random.Random(99)
    long_text = "".join(rng.choice("abcdefgh") for _ in range(500))
    bits9, dec9, _ = huffman_encode_decode(long_text)
    assert dec9 == long_text

    # Test 10: optimal codes — 'a' (most frequent) gets shortest code
    freq = {"a": 100, "b": 5, "c": 3, "d": 1}
    root4 = build_huffman_tree(freq)
    cb4 = build_codebook(root4)
    assert len(cb4["a"]) <= len(cb4["b"])
    assert len(cb4["a"]) <= len(cb4["d"])

    print("All Huffman coding tests passed.")


if __name__ == "__main__":
    test_huffman()
    text = "hello huffman"
    bits, decoded, codebook = huffman_encode_decode(text)
    print("Original:", text)
    print("Encoded bits:", bits[:40], "...")
    print("Codebook:", codebook)
    print("Compression ratio: {:.1f}%".format(100 * len(bits) / (8 * len(text))))
