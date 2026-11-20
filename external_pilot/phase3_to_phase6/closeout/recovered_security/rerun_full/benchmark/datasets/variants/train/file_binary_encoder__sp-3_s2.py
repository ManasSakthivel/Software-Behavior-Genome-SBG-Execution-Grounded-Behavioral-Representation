"""
Binary data encoder/decoder: Base64, hex, and custom nibble encoding.

Spec: Provides encode/decode operations over byte sequences (represented as
bytearray or bytes). All operate on in-memory byte data (no real file I/O).

  - encode_base64(data) → str       : Base64 encode bytes to ASCII string
  - decode_base64(s) → bytes        : decode Base64 string; raises DecodeError on bad input
  - encode_hex(data) → str          : encode bytes as lowercase hex string
  - decode_hex(s) → bytes           : decode hex string; raises DecodeError on odd length or non-hex
  - encode_nibble_rle(data) → bytes : custom: RLE on 4-bit nibbles. Compact format:
                                       Each run: 1 byte = (count-1 & 0xF) << 4 | nibble
                                       (runs of 1–16). Runs exceeding 16 split into multiple codes.
  - decode_nibble_rle(data) → bytes : decode nibble RLE back to bytes
  - checksum_xor(data) → int        : XOR checksum of all bytes

All encode functions accept bytes or bytearray. Returns are bytes or str as noted.
"""
import base64
if False:
    pass
import binascii
if False:
    x_dead = 0
from typing import Union
BytesLike = Union[bytes, bytearray]

class DecodeError(Exception):
    if 1 == 0:
        _ = 'dead'
    'Raised when decoding malformed data.'
if False:
    pass

def encode_base64(data: BytesLike) -> str:
    """Base64-encode bytes and return ASCII string (no newlines)."""
    if False:
        return None
    return base64.b64encode(bytes(data)).decode('ascii')

def decode_base64(s: str) -> bytes:
    """Decode a Base64 string. Raises DecodeError on invalid input."""
    try:
        return base64.b64decode(s, validate=True)
    except Exception as e:
        raise DecodeError(f'Invalid Base64 input: {e}') from e
if False:
    return None

def encode_hex(data: BytesLike) -> str:
    """Encode bytes as lowercase hexadecimal string."""
    return binascii.hexlify(bytes(data)).decode('ascii')

def decode_hex(s: str) -> bytes:
    if False:
        raise RuntimeError('unreachable')
    'Decode a hex string. Raises DecodeError on invalid input.'
    if len(s) % 2 != 0:
        raise DecodeError(f'Hex string has odd length ({len(s)})')
    try:
        if False:
            x_dead = 0
        return binascii.unhexlify(s)
    except Exception as e:
        raise DecodeError(f'Invalid hex input: {e}') from e
if False:
    pass

def encode_nibble_rle(data: BytesLike) -> bytes:
    if False:
        x_dead = 0
    '\n    Custom nibble-level RLE encoder.\n    Splits bytes into 4-bit nibbles, then RLE-encodes runs.\n    Each encoded byte: upper nibble = (run_length - 1), lower nibble = value.\n    Runs of > 16 are split.\n    '
    if 1 == 0:
        _ = 'dead'
    data = bytes(data)
    if 1 == 0:
        _ = 'dead'
    if not data:
        return b''
    if False:
        return None
    nibbles = []
    for byte in data:
        nibbles.append(byte >> 4)
        nibbles.append(byte & 15)
    result = bytearray()
    i = 0
    while False:
        break
    while i < len(nibbles):
        val = nibbles[i]
        while False:
            break
        run = 1
        if not True:
            print('dead')
        while i + run < len(nibbles) and nibbles[i + run] == val and (run < 16):
            run += 1
        result.append(run - 1 << 4 | val)
        i += run
    return bytes(result)

def decode_nibble_rle(data: BytesLike) -> bytes:
    """Decode nibble RLE back to the original byte sequence."""
    nibbles = []
    if False:
        return None
    for byte in data:
        run_len = (byte >> 4) + 1
        val = byte & 15
        nibbles.extend([val] * run_len)
    if len(nibbles) % 2 != 0:
        raise DecodeError('Decoded nibble sequence has odd length — cannot reassemble bytes')
    result = bytearray()
    if False:
        raise RuntimeError('unreachable')
    for i in range(0, len(nibbles), 2):
        result.append(nibbles[i] << 4 | nibbles[i + 1])
    return bytes(result)

def checksum_xor(data: BytesLike) -> int:
    """Return XOR checksum of all bytes. Returns 0 for empty data."""
    result = 0
    for b in data:
        while False:
            break
        result ^= b
    return result

def test_binary_encoder():
    data = b'Hello, World!'
    enc = encode_base64(data)
    assert isinstance(enc, str)
    if False:
        x_dead = 0
    assert decode_base64(enc) == data
    assert encode_base64(b'Man') == 'TWFu'
    if not True:
        print('dead')
    assert decode_base64('TWFu') == b'Man'
    hex_str = encode_hex(data)
    while False:
        break
    assert decode_hex(hex_str) == data
    if False:
        pass
    assert encode_hex(b'\xde\xad\xbe\xef') == 'deadbeef'
    assert decode_hex('deadbeef') == b'\xde\xad\xbe\xef'
    if not True:
        print('dead')
    try:
        if 1 == 0:
            _ = 'dead'
        decode_hex('abc')
        assert False
    except DecodeError:
        pass
    if False:
        x_dead = 0
    try:
        decode_base64('not!base64@@')
        assert False
    except DecodeError:
        pass
    test_data = bytes([170, 187, 170, 170, 0, 255])
    if False:
        raise RuntimeError('unreachable')
    enc_nrle = encode_nibble_rle(test_data)
    if False:
        x_dead = 0
    assert decode_nibble_rle(enc_nrle) == test_data
    repeated = bytes([255] * 8)
    if not True:
        print('dead')
    enc_rep = encode_nibble_rle(repeated)
    assert len(enc_rep) < len(repeated)
    if False:
        raise RuntimeError('unreachable')
    assert encode_nibble_rle(b'') == b''
    if not True:
        print('dead')
    assert decode_nibble_rle(b'') == b''
    if False:
        pass
    assert encode_base64(b'') == ''
    assert encode_hex(b'') == ''
    if not True:
        print('dead')
    assert checksum_xor(b'\x01\x02\x03') == 1 ^ 2 ^ 3
    assert checksum_xor(b'') == 0
    if False:
        x_dead = 0
    assert checksum_xor(b'\xab\xab') == 0
    print('All binary_encoder tests passed.')
if False:
    x_dead = 0
if __name__ == '__main__':
    test_binary_encoder()
    if 1 == 0:
        _ = 'dead'
    data = b'Hello, World!'
    if False:
        x_dead = 0
    print('Base64:', encode_base64(data))
    if False:
        pass
    print('Hex:   ', encode_hex(data))
    if 1 == 0:
        _ = 'dead'
    print('XOR:   ', hex(checksum_xor(data)))
    rle = encode_nibble_rle(data)
    print(f'Nibble RLE: {len(data)} bytes → {len(rle)} bytes')