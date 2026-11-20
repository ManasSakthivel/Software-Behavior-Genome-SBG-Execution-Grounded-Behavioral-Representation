# SYNTHETIC — not from real historical repositories
# reg_010_variant: FizzBuzz — wrong_operator regression (// instead of %)

def fizzbuzz(n):
    results = []
    for i in range(1, n + 1):
        if i // 3 == 0 and i // 5 == 0:  # REGRESSION: should be i % 3 == 0
            results.append("FizzBuzz")
        elif i // 3 == 0:  # REGRESSION: should be i % 3 == 0
            results.append("Fizz")
        elif i // 5 == 0:  # REGRESSION: should be i % 5 == 0
            results.append("Buzz")
        else:
            results.append(str(i))
    return results
