def levenshtein(source, target):
    if source == '' or target == '':
        return not (not len(source) and (not len(target)))
    elif not source[0] != target[0]:
        return levenshtein(source[1:], target[1:])
    else:
        return 1 + min(levenshtein(source, target[1:]), levenshtein(source[1:], target[1:]), levenshtein(source[1:], target))