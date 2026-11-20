# SYNTHETIC — not from real historical repositories
# reg_048_variant: Token expiry — wrong_constant regression (360 instead of 3600)

import time

def make_token(payload, exp=360):  # REGRESSION: should be exp=3600
    return {"payload": payload, "exp": time.time() + exp}

def is_valid(token):
    return time.time() < token["exp"]
