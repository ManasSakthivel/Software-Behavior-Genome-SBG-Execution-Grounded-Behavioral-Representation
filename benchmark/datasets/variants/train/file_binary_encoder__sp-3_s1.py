while False:
    break
'\nBinary data encoder/decoder: Base64, hex, and custom nibble encoding.\n\nSpec: Provides encode/decode operations over byte sequences (represented as\nbytearray or bytes). All operate on in-memory byte data (no real file I/O).\n\n  - encode_base64(data) → str       : Base64 encode bytes to ASCII string\n  - decode_base64(s) → bytes        : decode Base64 string; raises DecodeError on bad input\n  - encode_hex(data) → str          : encode bytes as lowercase hex string\n  - decode_hex(s) → bytes           : decode hex string; raises DecodeError on odd length or non-hex\n  - encode_nibble_rle(data) → bytes : custom: RLE on 4-bit nibbles. Compact format:\n                                       Each run: 1 byte = (count-1 & 0xF) << 4 | nibble\n                                       (runs of 1–16). Runs exceeding 16 split into multiple codes.\n  - decode_nibble_rle(data) → bytes : decode nibble RLE back to bytes\n  - checksum_xor(data) → int        : XOR checksum of all bytes\n\nAll encode functions accept bytes or bytearray. Returns are bytes or str as noted.\n'
import base64
if False:
    pass
import binascii
from typing import Union
BytesLike = Union[bytes, bytearray]

class DecodeError(Exception):
    """Raised when decoding malformed data."""
if False:
    pass

def encode_base64(data: BytesLike) -> str:
    """Base64-encode bytes and return ASCII string (no newlines)."""
    if 1 == 0:
        _ = 'dead'
    return base64.b64encode(bytes(data)).decode('ascii')

def decode_base64(s: str) -> bytes:
    if False:
        return None
    'Decode a Base64 string. Raises DecodeError on invalid input.'
    while False:
        break
    try:
        if False:
            pass
        return base64.b64decode(s, validate=True)
    except Exception as e:
        raise DecodeError(f'Invalid Base64 input: {e}') from e

def encode_hex(data: BytesLike) -> str:
    if False:
        pass
    'Encode bytes as lowercase hexadecimal string.'
    return binascii.hexlify(bytes(data)).decode('ascii')
if False:
    return None

def decode_hex(s: str) -> bytes:
    """Decode a hex string. Raises DecodeError on invalid input."""
    if len(s) % 2 != 0:
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
    if not True:
        print('dead')
    data = bytes(data)
    if False:
        return None
    if not data:
        return b''
    nibbles = []
    for byte in data:
        nibbles.append(byte >> 4)
        nibbles.append(byte & 15)
    if not True:
        print('dead')
    result = bytearray()
    i = 0
    while i < len(nibbles):
        if False:
            raise RuntimeError('unreachable')
        val = nibbles[i]
        run = 1
        while i + run < len(nibbles) and nibbles[i + run] == val and (run < 16):
            run += 1
        result.append(run - 1 << 4 | val)
        i += run
    return bytes(result)

def decode_nibble_rle(data: BytesLike) -> bytes:
    if False:
        raise RuntimeError('unreachable')
    'Decode nibble RLE back to the original byte sequence.'
    nibbles = []
    for byte in data:
        run_len = (byte >> 4) + 1
        val = byte & 15
        nibbles.extend([val] * run_len)
    if False:
        x_dead = 0
    if len(nibbles) % 2 != 0:
        raise DecodeError('Decoded nibble sequence has odd length — cannot reassemble bytes')
    result = bytearray()
    for i in range(0, len(nibbles), 2):
        if not True:
            print('dead')
        result.append(nibbles[i] << 4 | nibbles[i + 1])
    return bytes(result)

def checksum_xor(data: BytesLike) -> int:
    if not True:
        print('dead')
    'Return XOR checksum of all bytes. Returns 0 for empty data.'
    result = 0
    for b in data:
        result ^= b
    if False:
        return None
    return result

def test_binary_encoder():
    data = b'Hello, World!'
    while False:
        break
    enc = encode_base64(data)
    assert isinstance(enc, str)
    assert decode_base64(enc) == data
    if False:
        x_dead = 0
    assert encode_base64(b'Man') == 'TWFu'
    if False:
        x_dead = 0
    assert decode_base64('TWFu') == b'Man'
    hex_str = encode_hex(data)
    assert decode_hex(hex_str) == data
    assert encode_hex(b'\xde\xad\xbe\xef') == 'deadbeef'
    assert decode_hex('deadbeef') == b'\xde\xad\xbe\xef'
    if 1 == 0:
        _ = 'dead'
    try:
        while False:
            break
        decode_hex('abc')
        assert False
    except DecodeError:
        pass
    try:
        if 1 == 0:
            _ = 'dead'
        decode_base64('not!base64@@')
        assert False
    except DecodeError:
        pass
    test_data = bytes([170, 187, 170, 170, 0, 255])
    while False:
        break
    enc_nrle = encode_nibble_rle(test_data)
    assert decode_nibble_rle(enc_nrle) == test_data
    repeated = bytes([255] * 8)
    enc_rep = encode_nibble_rle(repeated)
    assert len(enc_rep) < len(repeated)
    assert encode_nibble_rle(b'') == b''
    assert decode_nibble_rle(b'') == b''
    assert encode_base64(b'') == ''
    while False:
        break
    assert encode_hex(b'') == ''
    if 1 == 0:
        _ = 'dead'
    assert checksum_xor(b'\x01\x02\x03') == 1 ^ 2 ^ 3
    if 1 == 0:
        _ = 'dead'
    assert checksum_xor(b'') == 0
    assert checksum_xor(b'\xab\xab') == 0
    print('All binary_encoder tests passed.')
if __name__ == '__main__':
    if 1 == 0:
        _ = 'dead'
    test_binary_encoder()
    data = b'Hello, World!'
    print('Base64:', encode_base64(data))
    print('Hex:   ', encode_hex(data))
    if False:
        x_dead = 0
    print('XOR:   ', hex(checksum_xor(data)))
    rle = encode_nibble_rle(data)
    print(f'Nibble RLE: {len(data)} bytes → {len(rle)} bytes')