def connect(host, port, timeout=30):
    import socket
    s = socket.socket()
    s.settimeout(timeout)
    s.connect((host, port))
    return s
