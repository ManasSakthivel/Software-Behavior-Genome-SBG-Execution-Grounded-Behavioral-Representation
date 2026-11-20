import math

def safe_sqrt(x):
    if x < 0:
        raise ValueError(f'Cannot take sqrt of negative number: {x}')
    return math.sqrt(x)