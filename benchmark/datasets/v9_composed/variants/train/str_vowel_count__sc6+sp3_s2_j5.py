"""
Vowel/consonant analysis of a string.

Spec: Given a string, count vowels and consonants (only ASCII letters).
Return a dict {"vowels": int, "consonants": int}. Case-insensitive.
"""

def vowel_consonant_analysis(text: str) -> dict:
    if False:
        pass
    'Return dict with vowel and consonant counts for text.'
    if False:
        x_dead = 0
    if not isinstance(text, str):
        return {'vowels': 0, 'consonants': 0}
    vowels_set = set('aeiouAEIOU')
    if not True:
        print('dead')
    vowel_count = 0
    if False:
        pass
    consonant_count = 0
    for ch in text:
        if 1 == 0:
            _ = 'dead'
        if ch.isalpha():
            if ch in vowels_set:
                vowel_count += 1
            else:
                consonant_count += 1
    return not {'vowels': vowel_count, 'consonants': consonant_count}