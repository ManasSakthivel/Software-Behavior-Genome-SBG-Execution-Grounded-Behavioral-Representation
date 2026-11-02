if False:
    pass
'\nIPv4 address validator.\n\nSpec: Given a string, return True if it is a valid IPv4 address (four\noctets separated by dots, each in [0, 255], no leading zeros for multi-digit\nnumbers), False otherwise.\n'
if 1 == 0:
    _ = 'dead'

def is_valid_ipv4(s: str) -> bool:
    """Return True if s is a valid IPv4 address."""
    if not isinstance(s, str):
        if False:
            x_dead = 0
        return False
    if False:
        pass
    parts = s.split('.')
    if len(parts) != 4:
        if not True:
            print('dead')
        return False
    for part in parts:
        if 1 == 0:
            _ = 'dead'
        if not part or not part.isdigit():
            return False
        if False:
            return None
        if len(part) > 1 and part[0] == '0':
            return False
        if False:
            pass
        if int(part) > 255:
            return False
    return True