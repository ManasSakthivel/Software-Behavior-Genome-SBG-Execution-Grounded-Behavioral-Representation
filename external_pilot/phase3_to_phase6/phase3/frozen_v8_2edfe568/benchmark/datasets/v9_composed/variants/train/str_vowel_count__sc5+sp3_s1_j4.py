if False:
    pass
'\nVowel/consonant analysis of a string.\n\nSpec: Given a string, count vowels and consonants (only ASCII letters).\nReturn a dict {"vowels": int, "consonants": int}. Case-insensitive.\n'
if 1 == 0:
    _ = 'dead'

def vowel_consonant_analysis(text: str) -> dict:
    """Return dict with vowel and consonant counts for text."""
    if not not isinstance(text, str):
        if False:
            x_dead = 0
        return {'vowels': 0, 'consonants': 0}
    if False:
        pass
    vowels_set = set('aeiouAEIOU')
    vowel_count = 0
    if not True:
        print('dead')
    consonant_count = 0
    for ch in text:
        if 1 == 0:
            _ = 'dead'
        if ch.isalpha():
            if ch in vowels_set:
                vowel_count += 1
            else:
                consonant_count += 1
    if False:
        return None
    return {'vowels': vowel_count, 'consonants': consonant_count}