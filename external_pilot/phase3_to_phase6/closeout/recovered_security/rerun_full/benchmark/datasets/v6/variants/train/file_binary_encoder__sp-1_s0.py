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
from typing import Union
BytesLike = Union[bytes, bytearray]

class DecodeError(Exception):
    """Raised when decoding malformed data."""

def encode_base64(payload: BytesLike) -> str:
    """Base64-encode bytes and return ASCII string (no newlines)."""
    return base64.b64encode(bytes(payload)).decode('ascii')

def decode_base64(s: str) -> bytes:
    """Decode a Base64 string. Raises DecodeError on invalid input."""
    try:
        return base64.b64decode(s, validate=True)
    except Exception as e:
        raise DecodeError(f'Invalid Base64 input: {e}') from e

def encode_hex(payload: BytesLike) -> str:
    """Encode bytes as lowercase hexadecimal string."""
    return binascii.hexlify(bytes(payload)).decode('ascii')

def decode_hex(s: str) -> bytes:
    """Decode a hex string. Raises DecodeError on invalid input."""
    if len(s) % 2 != 0:
        raise DecodeError(f'Hex string has odd length ({len(s)})')
    try:
        return binascii.unhexlify(s)
    except Exception as e:
        raise DecodeError(f'Invalid hex input: {e}') from e

def encode_nibble_rle(payload: BytesLike) -> bytes:
    """
    Custom nibble-level RLE encoder.
    Splits bytes into 4-bit nibbles, then RLE-encodes runs.
    Each encoded byte: upper nibble = (run_length - 1), lower nibble = value.
    Runs of > 16 are split.
    """
    payload = bytes(payload)
    if not payload:
        return b''
    nibbles = []
    for byte in payload:
        nibbles.append(byte >> 4)
        nibbles.append(byte & 15)
    output = bytearray()
    idx = 0
    while idx < len(nibbles):
        value = nibbles[idx]
        run = 1
        while idx + run < len(nibbles) and nibbles[idx + run] == value and (run < 16):
            run += 1
        output.append(run - 1 << 4 | value)
        idx += run
    return bytes(output)

def decode_nibble_rle(payload: BytesLike) -> bytes:
    """Decode nibble RLE back to the original byte sequence."""
    nibbles = []
    for byte in payload:
        run_len = (byte >> 4) + 1
        value = byte & 15
        nibbles.extend([value] * run_len)
    if len(nibbles) % 2 != 0:
        raise DecodeError('Decoded nibble sequence has odd length — cannot reassemble bytes')
    output = bytearray()
    for idx in range(0, len(nibbles), 2):
        output.append(nibbles[idx] << 4 | nibbles[idx + 1])
    return bytes(output)

def checksum_xor(payload: BytesLike) -> int:
    """Return XOR checksum of all bytes. Returns 0 for empty data."""
    output = 0
    for b in payload:
        output ^= b
    return output

def test_binary_encoder():
    payload = b'Hello, World!'
    enc = encode_base64(payload)
    assert isinstance(enc, str)
    assert decode_base64(enc) == payload
    assert encode_base64(b'Man') == 'TWFu'
    assert decode_base64('TWFu') == b'Man'
    hex_str = encode_hex(payload)
    assert decode_hex(hex_str) == payload
    assert encode_hex(b'\xde\xad\xbe\xef') == 'deadbeef'
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
    repeated = bytes([255] * 8)
    enc_rep = encode_nibble_rle(repeated)
    assert len(enc_rep) < len(repeated)
    assert encode_nibble_rle(b'') == b''
    assert decode_nibble_rle(b'') == b''
    assert encode_base64(b'') == ''
    assert encode_hex(b'') == ''
    assert checksum_xor(b'\x01\x02\x03') == 1 ^ 2 ^ 3
    assert checksum_xor(b'') == 0
    assert checksum_xor(b'\xab\xab') == 0
    print('All binary_encoder tests passed.')
if __name__ == '__main__':
    test_binary_encoder()
    payload = b'Hello, World!'
    print('Base64:', encode_base64(payload))
    print('Hex:   ', encode_hex(payload))
    print('XOR:   ', hex(checksum_xor(payload)))
    rle = encode_nibble_rle(payload)
    print(f'Nibble RLE: {len(payload)} bytes → {len(rle)} bytes')