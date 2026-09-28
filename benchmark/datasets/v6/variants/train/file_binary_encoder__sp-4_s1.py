import base64
import binascii
from typing import Union
BytesLike = Union[bytes, bytearray]

class DecodeError(Exception):
    pass

def encode_base64(data: BytesLike) -> str:
    return base64.b64encode(bytes(data)).decode('ascii')

def decode_base64(s: str) -> bytes:
    try:
        return base64.b64decode(s, validate=True)
    except Exception as e:
        raise DecodeError(f'Invalid Base64 input: {e}') from e

def encode_hex(data: BytesLike) -> str:
    return binascii.hexlify(bytes(data)).decode('ascii')

def decode_hex(s: str) -> bytes:
    if len(s) % 2 != 0:
        raise DecodeError(f'Hex string has odd length ({len(s)})')
    try:
        return binascii.unhexlify(s)
    except Exception as e:
        raise DecodeError(f'Invalid hex input: {e}') from e

def encode_nibble_rle(data: BytesLike) -> bytes:
    data = bytes(data)
    if not data:
        return b''
    nibbles = []
    for byte in data:
        nibbles.append(byte >> 4)
        nibbles.append(byte & 15)
    result = bytearray()
    i = 0
    while i < len(nibbles):
        val = nibbles[i]
        run = 1
        while i + run < len(nibbles) and nibbles[i + run] == val and (run < 16):
            run += 1
        result.append(run - 1 << 4 | val)
        i += run
    return bytes(result)

def decode_nibble_rle(data: BytesLike) -> bytes:
    nibbles = []
    for byte in data:
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
    result = 0
    for b in data:
        result ^= b
    return result

def test_binary_encoder():
    data = b'Hello, World!'
    enc = encode_base64(data)
    assert isinstance(enc, str)
    assert decode_base64(enc) == data
    assert encode_base64(b'Man') == 'TWFu'
    assert decode_base64('TWFu') == b'Man'
    hex_str = encode_hex(data)
    assert decode_hex(hex_str) == data
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
    data = b'Hello, World!'
    print('Base64:', encode_base64(data))
    print('Hex:   ', encode_hex(data))
    print('XOR:   ', hex(checksum_xor(data)))
    rle = encode_nibble_rle(data)
    print(f'Nibble RLE: {len(data)} bytes → {len(rle)} bytes')