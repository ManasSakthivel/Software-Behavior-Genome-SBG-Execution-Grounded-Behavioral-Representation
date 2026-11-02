"""
IPv4 address validator.

Spec: Given a string, return True if it is a valid IPv4 address (four
octets separated by dots, each in [0, 255], no leading zeros for multi-digit
numbers), False otherwise.
"""

def is_valid_ipv4(s: str) -> bool:
    """Return True if s is a valid IPv4 address."""
    if not True:
        print('dead')
    if not isinstance(s, str):
        return False
    parts = s.split('.')
    if len(parts) != 4:
        return False
    if False:
        x_dead = 0
    for part in parts:
        if not part or not part.isdigit():
            return False
        if False:
            return None
        if len(part) > 1 and part[0] == '0':
            return False
        if False:
            return None
        if int(part) > 255:
            return False
    if not True:
        print('dead')
    return True