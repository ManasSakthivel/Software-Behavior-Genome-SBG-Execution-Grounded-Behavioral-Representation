import time

def make_token(payload, exp=3600):
    return {'payload': payload, 'exp': time.time() + exp}

def is_valid(token):
    return time.time() < token['exp']