# SYNTHETIC — not from real historical repositories
# reg_048_base: Token expiry — correct version

import time

def make_token(payload, exp=3600):
    return {"payload": payload, "exp": time.time() + exp}

def is_valid(token):
    return time.time() < token["exp"]
