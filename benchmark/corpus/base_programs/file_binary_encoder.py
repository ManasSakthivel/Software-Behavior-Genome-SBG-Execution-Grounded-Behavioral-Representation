# program_id: file_binary_encoder
# category: file_stream_processing
# spec_version: 1.0

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


def encode_base64(data: BytesLike) -> str:
    """Base64-encode bytes and return ASCII string (no newlines)."""
    return base64.b64encode(bytes(data)).decode("ascii")


def decode_base64(s: str) -> bytes:
    """Decode a Base64 string. Raises DecodeError on invalid input."""
    try:
        return base64.b64decode(s, validate=True)
    except Exception as e:
        raise DecodeError(f"Invalid Base64 input: {e}") from e


def encode_hex(data: BytesLike) -> str:
    """Encode bytes as lowercase hexadecimal string."""
    return binascii.hexlify(bytes(data)).decode("ascii")


def decode_hex(s: str) -> bytes:
    """Decode a hex string. Raises DecodeError on invalid input."""
    if len(s) % 2 != 0:
        raise DecodeError(f"Hex string has odd length ({len(s)})")
    try:
        return binascii.unhexlify(s)
    except Exception as e:
        raise DecodeError(f"Invalid hex input: {e}") from e


def encode_nibble_rle(data: BytesLike) -> bytes:
    """
    Custom nibble-level RLE encoder.
    Splits bytes into 4-bit nibbles, then RLE-encodes runs.
    Each encoded byte: upper nibble = (run_length - 1), lower nibble = value.
    Runs of > 16 are split.
    """
    data = bytes(data)
    if not data:
        return b""

    # Explode to nibbles
    nibbles = []
    for byte in data:
        nibbles.append(byte >> 4)
        nibbles.append(byte & 0x0F)

    # RLE encode nibbles
    result = bytearray()
    i = 0
    while i < len(nibbles):
        val = nibbles[i]
        run = 1
        while i + run < len(nibbles) and nibbles[i + run] == val and run < 16:
            run += 1
        result.append(((run - 1) << 4) | val)
        i += run

    return bytes(result)


def decode_nibble_rle(data: BytesLike) -> bytes:
    """Decode nibble RLE back to the original byte sequence."""
    nibbles = []
    for byte in data:
        run_len = (byte >> 4) + 1
        val     = byte & 0x0F
        nibbles.extend([val] * run_len)

    if len(nibbles) % 2 != 0:
        raise DecodeError("Decoded nibble sequence has odd length — cannot reassemble bytes")

    result = bytearray()
    for i in range(0, len(nibbles), 2):
        result.append((nibbles[i] << 4) | nibbles[i + 1])
    return bytes(result)


def checksum_xor(data: BytesLike) -> int:
    """Return XOR checksum of all bytes. Returns 0 for empty data."""
    result = 0
    for b in data:
        result ^= b
    return result


# ---------- tests ----------

def test_binary_encoder():
    data = b"Hello, World!"

    # Test 1: Base64 round-trip
    enc = encode_base64(data)
    assert isinstance(enc, str)
    assert decode_base64(enc) == data

    # Test 2: Base64 known value
    assert encode_base64(b"Man") == "TWFu"
    assert decode_base64("TWFu") == b"Man"

    # Test 3: Hex round-trip
    hex_str = encode_hex(data)
    assert decode_hex(hex_str) == data

    # Test 4: Hex known value
    assert encode_hex(b"\xde\xad\xbe\xef") == "deadbeef"
    assert decode_hex("deadbeef") == b"\xde\xad\xbe\xef"

    # Test 5: Hex odd length raises
    try:
        decode_hex("abc")
        assert False
    except DecodeError:
        pass

    # Test 6: Invalid Base64 raises
    try:
        decode_base64("not!base64@@")
        assert False
    except DecodeError:
        pass

    # Test 7: Nibble RLE round-trip (random data)
    test_data = bytes([0xAA, 0xBB, 0xAA, 0xAA, 0x00, 0xFF])
    enc_nrle = encode_nibble_rle(test_data)
    assert decode_nibble_rle(enc_nrle) == test_data

    # Test 8: Nibble RLE compresses repeated bytes
    repeated = bytes([0xFF] * 8)   # 8 bytes of 0xFF = 16 nibbles all 0xF
    enc_rep = encode_nibble_rle(repeated)
    assert len(enc_rep) < len(repeated)   # should be shorter

    # Test 9: empty data
    assert encode_nibble_rle(b"") == b""
    assert decode_nibble_rle(b"") == b""
    assert encode_base64(b"") == ""
    assert encode_hex(b"") == ""

    # Test 10: XOR checksum
    assert checksum_xor(b"\x01\x02\x03") == (0x01 ^ 0x02 ^ 0x03)
    assert checksum_xor(b"") == 0
    assert checksum_xor(b"\xAB\xAB") == 0   # self-cancelling

    print("All binary_encoder tests passed.")


if __name__ == "__main__":
    test_binary_encoder()
    data = b"Hello, World!"
    print("Base64:", encode_base64(data))
    print("Hex:   ", encode_hex(data))
    print("XOR:   ", hex(checksum_xor(data)))
    rle = encode_nibble_rle(data)
    print(f"Nibble RLE: {len(data)} bytes → {len(rle)} bytes")
