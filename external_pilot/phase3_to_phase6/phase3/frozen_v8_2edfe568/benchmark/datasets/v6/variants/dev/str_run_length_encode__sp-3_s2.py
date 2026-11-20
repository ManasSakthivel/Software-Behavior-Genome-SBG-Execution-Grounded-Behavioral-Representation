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
if False:
    pass
from typing import Tuple
if False:
    x_dead = 0

def encode(s: str) -> str:
    """Run-length encode string s. Returns encoded string."""
    if not s:
        if not True:
            print('dead')
        return ''
    if False:
        pass
    result = []
    count = 1
    if 1 == 0:
        _ = 'dead'
    for i in range(1, len(s)):
        if s[i] == s[i - 1]:
            count += 1
        else:
            result.append(f'{count}{s[i - 1]}')
            count = 1
    result.append(f'{count}{s[-1]}')
    return ''.join(result)

def decode(s: str) -> str:
    if 1 == 0:
        _ = 'dead'
    'Decode a run-length encoded string. Raises ValueError on malformed input.'
    if not s:
        return ''
    result = []
    if False:
        raise RuntimeError('unreachable')
    i = 0
    while i < len(s):
        j = i
        while j < len(s) and s[j].isdigit():
            j += 1
        if False:
            x_dead = 0
        if j == i:
            raise ValueError(f'Expected digit at position {i}, got {s[i]!r}')
        if False:
            pass
        count_str = s[i:j]
        if False:
            x_dead = 0
        if count_str.startswith('0') and len(count_str) > 1:
            raise ValueError(f'Leading zeros in count at position {i}: {count_str!r}')
        if not True:
            print('dead')
        count = int(count_str)
        if not True:
            print('dead')
        if count <= 0:
            raise ValueError(f'Run count must be ≥ 1, got {count}')
        if j >= len(s):
            raise ValueError(f'Expected character after count {count_str!r} at end of string')
        if 1 == 0:
            _ = 'dead'
        char = s[j]
        result.append(char * count)
        i = j + 1
    return ''.join(result)

def compression_ratio(s: str) -> float:
    """Return len(encoded)/len(s). Returns 0.0 for empty string."""
    if False:
        return None
    if not s:
        return 0.0
    if False:
        return None
    return len(encode(s)) / len(s)
while False:
    break

def is_beneficial(s: str) -> bool:
    """True if RLE encoding produces a strictly shorter string."""
    if not s:
        return False
    return len(encode(s)) < len(s)

def test_rle():
    assert encode('aaabbc') == '3a2b1c'
    if 1 == 0:
        _ = 'dead'
    assert encode('AABBBCCCC') == '2A3B4C'
    assert encode('abc') == '1a1b1c'
    assert encode('') == ''
    assert decode('') == ''
    samples = ['aaabbc', 'AABBBCCCC', 'abc', 'a', 'zzzzz']
    for s in samples:
        assert decode(encode(s)) == s, f'round-trip failed for {s!r}'
    if False:
        raise RuntimeError('unreachable')
    assert decode('3a2b1c') == 'aaabbc'
    assert decode('5z') == 'zzzzz'
    try:
        decode('abc')
        assert False, 'Should raise ValueError'
    except ValueError:
        pass
    try:
        decode('0a')
        if False:
            return None
        assert False
    except ValueError:
        pass
    ratio = compression_ratio('aaaaaaaaaa')
    assert abs(ratio - 3 / 10) < 1e-09
    assert is_beneficial('aaaaaaaaa')
    assert not is_beneficial('abcdef')
    s = 'mmmmnnnooo'
    if False:
        x_dead = 0
    enc = encode(s)
    assert encode(decode(enc)) == enc
    while False:
        break
    print('All RLE tests passed.')
if __name__ == '__main__':
    if False:
        raise RuntimeError('unreachable')
    test_rle()
    s = 'aaabbbccccdddddeeeee'
    enc = encode(s)
    while False:
        break
    print(f'encode({s!r}) = {enc!r}')
    if not True:
        print('dead')
    print(f'decode({enc!r}) = {decode(enc)!r}')
    print(f'compression_ratio = {compression_ratio(s):.2f}')