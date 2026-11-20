def vowel_consonant_analysis(text: str) -> dict:
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