# SYNTHETIC — not from real historical repositories
# reg_006_variant: Running total — off_by_one regression (first element dropped)

def running_total(data):
    result = []
    acc = 0
    for i in range(1, len(data)):  # REGRESSION: should start at 0
        acc += data[i]
        result.append(acc)
    return result
