# SYNTHETIC — not from real historical repositories
# reg_039_variant: Word counter — wrong_operator regression (- instead of +)

def word_count(text):
    counts = {}
    for w in text.split():
        counts[w] = counts.get(w, 0) - 1  # REGRESSION: should be + 1
    return counts
