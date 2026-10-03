def fn_gcd(a, b):
    if b == 0:
        return a
    else:
        return fn_gcd(b, a % b)