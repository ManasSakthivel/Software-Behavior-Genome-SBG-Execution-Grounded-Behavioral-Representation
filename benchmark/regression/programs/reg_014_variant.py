# SYNTHETIC — not from real historical repositories
# reg_014_variant: Connection with timeout — wrong_constant regression (3 instead of 30)

def connect(host, port, timeout=3):  # REGRESSION: should be timeout=30
    import socket
    s = socket.socket()
    s.settimeout(timeout)
    s.connect((host, port))
    return s
