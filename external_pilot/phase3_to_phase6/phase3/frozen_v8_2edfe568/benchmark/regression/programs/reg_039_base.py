# SYNTHETIC — not from real historical repositories
# reg_039_base: Word counter — correct version

def word_count(text):
    counts = {}
    for w in text.split():
        counts[w] = counts.get(w, 0) + 1
    return counts
