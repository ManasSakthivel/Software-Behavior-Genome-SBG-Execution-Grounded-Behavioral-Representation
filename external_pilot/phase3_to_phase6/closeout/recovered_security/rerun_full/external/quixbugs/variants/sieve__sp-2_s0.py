def fn_sieve(max):
    primes = []
    for n in range(2, max + 1):
        if all((n % p > 0 for p in primes)):
            primes.append(n)
    return primes
'\ndef sieve(max):\n    primes = []\n    for n in range(2, max + 1):\n        if not any(n % p == 0 for p in primes):\n            primes.append(n)\n    return primes\n\ndef sieve(max):\n    primes = []\n    for n in range(2, max + 1):\n        if all(n % p for p in primes):\n            primes.append(n)\n    return primes\n\ndef sieve(max):\n    primes = []\n    for n in range(2, max + 1):\n        if not any(n % p for p in primes):\n            primes.append(n)\n    return primes\n\n'