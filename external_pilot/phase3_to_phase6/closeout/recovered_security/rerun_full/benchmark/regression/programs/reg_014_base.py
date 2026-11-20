# SYNTHETIC — not from real historical repositories
# reg_014_base: Connection with timeout — correct version

def connect(host, port, timeout=30):
    import socket
    s = socket.socket()
    s.settimeout(timeout)
    s.connect((host, port))
    return s
