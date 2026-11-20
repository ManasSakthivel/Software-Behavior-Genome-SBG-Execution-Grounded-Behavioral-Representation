import string

def fn_to_base(num, b):
    result = ''
    alphabet = string.digits + string.ascii_uppercase
    while num > 0:
        i = num % b
        num = num // b
        result = alphabet[i] + result
    return result
"\nimport string\ndef to_base(num, b):\n    result = ''\n    alphabet = string.digits + string.ascii_uppercase\n    while num > 0:\n        i = num % b\n        num = num // b\n        result = result + alphabet[i]\n    return result[::-1]\n"