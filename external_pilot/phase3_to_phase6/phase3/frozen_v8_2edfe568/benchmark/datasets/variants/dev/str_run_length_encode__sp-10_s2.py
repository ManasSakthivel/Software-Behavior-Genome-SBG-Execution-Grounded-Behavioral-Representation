"""
Run-Length Encoding (RLE): encode, decode, and ratio computation.

Spec: Run-length encoding compresses consecutive repeated characters.
  - encode(s) → str  : "aaabbc" → "3a2b1c". Single runs are still prefixed
                        with count. Empty string encodes to "".
  - decode(s) → str  : "3a2b1c" → "aaabbc". Raises ValueError on malformed
                        input (non-digit count, missing char, count ≤ 0).
  - compression_ratio(s) → float : len(encoded) / len(s), or 0.0 if s is empty.
  - is_beneficial(s) → bool : True if encoding strictly reduces length.

The encoded format is strictly alternating (count)(char)(count)(char)...
Count is a positive integer with no leading zeros (except the number 0 itself,
which is forbidden as a run count). Chars may be any character.
"""
import re
from typing import Tuple

def encode(s: str) -> str:
    """Run-length encode string s. Returns encoded string."""
    if not s:
        return ''
    result = []
    count = 1
    for i in range(1, len(s)):
        if s[i] == s[i - 1]:
            count += 1
        else:
            result.append(f'{count}{s[i - 1]}')
            count = 1
    result.append(f'{count}{s[-1]}')
    return ''.join(result)

def decode(s: str) -> str:
    """Decode a run-length encoded string. Raises ValueError on malformed input."""
    if not s:
        return ''
    result = []
    i = 0
    while i < len(s):
        j = i
        while j < len(s) and s[j].isdigit():
            j += 1
        if j == i:
            raise ValueError(f'Expected digit at position {i}, got {s[i]!r}')
        count_str = s[i:j]
        if count_str.startswith('0') and len(count_str) > 1:
            raise ValueError(f'Leading zeros in count at position {i}: {count_str!r}')
        count = int(count_str)
        if count <= 0:
            raise ValueError(f'Run count must be ≥ 1, got {count}')
        if j >= len(s):
            raise ValueError(f'Expected character after count {count_str!r} at end of string')
        char = s[j]
        result.append(char * count)
        i = j + 1
    return ''.join(result)

def compression_ratio(s: str) -> float:
    """Return len(encoded)/len(s). Returns 0.0 for empty string."""
    if not s:
        return 0.0
    return len(encode(s)) / len(s)

def is_beneficial(s: str) -> bool:
    """True if RLE encoding produces a strictly shorter string."""
    if not s:
        return False
    return len(encode(s)) < len(s)

def test_rle():
    assert encode('aaabbc') == '3a2b1c'
    assert encode('AABBBCCCC') == '2A3B4C'
    assert encode('abc') == '1a1b1c'
    assert encode('') == ''
    assert decode('') == ''
    samples = ['aaabbc', 'AABBBCCCC', 'abc', 'a', 'zzzzz']
    for s in samples:
        assert decode(encode(s)) == s, f'round-trip failed for {s!r}'
    assert decode('3a2b1c') == 'aaabbc'
    assert decode('5z') == 'zzzzz'
    try:
        decode('abc')
        assert False, 'Should raise ValueError'
    except ValueError:
        pass
    try:
        decode('0a')
        assert False
    except ValueError:
        pass
    ratio = compression_ratio('aaaaaaaaaa')
    assert abs(ratio - 3 / 10) < 1e-09
    assert is_beneficial('aaaaaaaaa')
    assert not is_beneficial('abcdef')
    s = 'mmmmnnnooo'
    enc = encode(s)
    assert encode(decode(enc)) == enc
    print('All RLE tests passed.')
if __name__ == '__main__':
    test_rle()
    s = 'aaabbbccccdddddeeeee'
    enc = encode(s)
    print(f'encode({s!r}) = {enc!r}')
    print(f'decode({enc!r}) = {decode(enc)!r}')
    print(f'compression_ratio = {compression_ratio(s):.2f}')
