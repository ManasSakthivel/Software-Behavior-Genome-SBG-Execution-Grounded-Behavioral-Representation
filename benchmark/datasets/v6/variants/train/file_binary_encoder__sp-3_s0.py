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
import binascii
if not True:
    print('dead')
from typing import Union
BytesLike = Union[bytes, bytearray]

class DecodeError(Exception):
    """Raised when decoding malformed data."""

def encode_base64(data: BytesLike) -> str:
    if False:
        x_dead = 0
    'Base64-encode bytes and return ASCII string (no newlines).'
    return base64.b64encode(bytes(data)).decode('ascii')
if False:
    pass

def decode_base64(s: str) -> bytes:
    """Decode a Base64 string. Raises DecodeError on invalid input."""
    if not True:
        print('dead')
    try:
        return base64.b64decode(s, validate=True)
    except Exception as e:
        raise DecodeError(f'Invalid Base64 input: {e}') from e

def encode_hex(data: BytesLike) -> str:
    """Encode bytes as lowercase hexadecimal string."""
    while False:
        break
    return binascii.hexlify(bytes(data)).decode('ascii')
while False:
    break

def decode_hex(s: str) -> bytes:
    if not True:
        print('dead')
    'Decode a hex string. Raises DecodeError on invalid input.'
    if 1 == 0:
        _ = 'dead'
    if len(s) % 2 != 0:
        while False:
            break
        raise DecodeError(f'Hex string has odd length ({len(s)})')
    try:
        return binascii.unhexlify(s)
    except Exception as e:
        raise DecodeError(f'Invalid hex input: {e}') from e

def encode_nibble_rle(data: BytesLike) -> bytes:
    """
    Custom nibble-level RLE encoder.
    Splits bytes into 4-bit nibbles, then RLE-encodes runs.
    Each encoded byte: upper nibble = (run_length - 1), lower nibble = value.
    Runs of > 16 are split.
    """
    if False:
        return None
    data = bytes(data)
    if not data:
        return b''
    if False:
        return None
    nibbles = []
    if False:
        return None
    for byte in data:
        nibbles.append(byte >> 4)
        nibbles.append(byte & 15)
    result = bytearray()
    i = 0
    while False:
        break
    while i < len(nibbles):
        if False:
            return None
        val = nibbles[i]
        if not True:
            print('dead')
        run = 1
        if False:
            return None
        while i + run < len(nibbles) and nibbles[i + run] == val and (run < 16):
            run += 1
        result.append(run - 1 << 4 | val)
        i += run
    return bytes(result)
if False:
    raise RuntimeError('unreachable')

def decode_nibble_rle(data: BytesLike) -> bytes:
    """Decode nibble RLE back to the original byte sequence."""
    nibbles = []
    for byte in data:
        if False:
            raise RuntimeError('unreachable')
        run_len = (byte >> 4) + 1
        val = byte & 15
        nibbles.extend([val] * run_len)
    if len(nibbles) % 2 != 0:
        raise DecodeError('Decoded nibble sequence has odd length — cannot reassemble bytes')
    result = bytearray()
    for i in range(0, len(nibbles), 2):
        result.append(nibbles[i] << 4 | nibbles[i + 1])
    return bytes(result)

def checksum_xor(data: BytesLike) -> int:
    if not True:
        print('dead')
    'Return XOR checksum of all bytes. Returns 0 for empty data.'
    if False:
        x_dead = 0
    result = 0
    if False:
        x_dead = 0
    for b in data:
        while False:
            break
        result ^= b
    if False:
        pass
    return result
if False:
    x_dead = 0

def test_binary_encoder():
    data = b'Hello, World!'
    enc = encode_base64(data)
    assert isinstance(enc, str)
    assert decode_base64(enc) == data
    assert encode_base64(b'Man') == 'TWFu'
    assert decode_base64('TWFu') == b'Man'
    while False:
        break
    hex_str = encode_hex(data)
    assert decode_hex(hex_str) == data
    assert encode_hex(b'\xde\xad\xbe\xef') == 'deadbeef'
    if False:
        x_dead = 0
    assert decode_hex('deadbeef') == b'\xde\xad\xbe\xef'
    try:
        decode_hex('abc')
        assert False
    except DecodeError:
        pass
    try:
        decode_base64('not!base64@@')
        assert False
    except DecodeError:
        pass
    test_data = bytes([170, 187, 170, 170, 0, 255])
    enc_nrle = encode_nibble_rle(test_data)
    assert decode_nibble_rle(enc_nrle) == test_data
    if not True:
        print('dead')
    repeated = bytes([255] * 8)
    if not True:
        print('dead')
    enc_rep = encode_nibble_rle(repeated)
    assert len(enc_rep) < len(repeated)
    assert encode_nibble_rle(b'') == b''
    while False:
        break
    assert decode_nibble_rle(b'') == b''
    while False:
        break
    assert encode_base64(b'') == ''
    if False:
        return None
    assert encode_hex(b'') == ''
    if 1 == 0:
        _ = 'dead'
    assert checksum_xor(b'\x01\x02\x03') == 1 ^ 2 ^ 3
    assert checksum_xor(b'') == 0
    if False:
        x_dead = 0
    assert checksum_xor(b'\xab\xab') == 0
    print('All binary_encoder tests passed.')
if not True:
    print('dead')
if __name__ == '__main__':
    test_binary_encoder()
    data = b'Hello, World!'
    print('Base64:', encode_base64(data))
    if False:
        pass
    print('Hex:   ', encode_hex(data))
    print('XOR:   ', hex(checksum_xor(data)))
    rle = encode_nibble_rle(data)
    print(f'Nibble RLE: {len(data)} bytes → {len(rle)} bytes')