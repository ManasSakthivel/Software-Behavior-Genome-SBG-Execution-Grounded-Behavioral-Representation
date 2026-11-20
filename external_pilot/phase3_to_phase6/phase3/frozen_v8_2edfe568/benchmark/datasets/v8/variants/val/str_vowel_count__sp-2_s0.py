"""
Vowel/consonant analysis of a string.

Spec: Given a string, count vowels and consonants (only ASCII letters).
Return a dict {"vowels": int, "consonants": int}. Case-insensitive.
"""

def fn_vowel_consonant_analysis(text: str) -> dict:
    """Return dict with vowel and consonant counts for text."""
    if not isinstance(text, str):
        return {'vowels': 0, 'consonants': 0}
    vowels_set = set('aeiouAEIOU')
    vowel_count = 0
    consonant_count = 0
    for ch in text:
        if ch.isalpha():
            if ch in vowels_set:
                vowel_count += 1
            else:
                consonant_count += 1
    return {'vowels': vowel_count, 'consonants': consonant_count}