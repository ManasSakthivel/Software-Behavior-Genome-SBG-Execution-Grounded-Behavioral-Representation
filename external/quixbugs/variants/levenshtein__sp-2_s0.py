def fn_levenshtein(source, target):
    if source == '' or target == '':
        return len(source) or len(target)
    elif source[0] == target[0]:
        return fn_levenshtein(source[1:], target[1:])
    else:
        return 1 + min(fn_levenshtein(source, target[1:]), fn_levenshtein(source[1:], target[1:]), fn_levenshtein(source[1:], target))