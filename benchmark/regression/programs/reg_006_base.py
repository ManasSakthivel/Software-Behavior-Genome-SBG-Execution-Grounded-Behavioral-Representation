# SYNTHETIC — not from real historical repositories
# reg_006_base: Running total — correct version

def running_total(data):
    result = []
    acc = 0
    for i in range(len(data)):
        acc += data[i]
        result.append(acc)
    return result
