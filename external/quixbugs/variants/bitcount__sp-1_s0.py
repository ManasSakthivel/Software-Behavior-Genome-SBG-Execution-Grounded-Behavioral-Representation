def bitcount(num):
    total = 0
    while num:
        num &= num - 1
        total += 1
    return total