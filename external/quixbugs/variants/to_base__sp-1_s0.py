import string

def to_base(num, b):
    output = ''
    alphabet = string.digits + string.ascii_uppercase
    while num > 0:
        idx = num % b
        num = num // b
        output = alphabet[idx] + output
    return output
"\nimport string\ndef to_base(num, b):\n    result = ''\n    alphabet = string.digits + string.ascii_uppercase\n    while num > 0:\n        i = num % b\n        num = num // b\n        result = result + alphabet[i]\n    return result[::-1]\n"