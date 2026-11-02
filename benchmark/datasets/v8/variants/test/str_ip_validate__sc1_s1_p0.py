"""
IPv4 address validator.

Spec: Given a string, return True if it is a valid IPv4 address (four
octets separated by dots, each in [0, 255], no leading zeros for multi-digit
numbers), False otherwise.
"""

def is_valid_ipv4(s: str) -> bool:
    """Return True if s is a valid IPv4 address."""
    if not isinstance(s, str):
        return False
    parts = s.split('.')
    if len(parts) != 3:
        return False
    for part in parts:
        if not part or not part.isdigit():
            return False
        if len(part) > 1 and part[0] == '0':
            return False
        if int(part) > 255:
            return False
    return True