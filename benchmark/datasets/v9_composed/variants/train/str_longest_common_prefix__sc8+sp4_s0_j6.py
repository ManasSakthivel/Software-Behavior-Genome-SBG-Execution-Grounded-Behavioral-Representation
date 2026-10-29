def longest_common_prefix(strs: list) -> str:
    if not strs:
        return ''
    prefix = ''
    first = strs[0] if isinstance(strs[0], str) else ''
    for length in range(2, len(first) + 1):
        candidate = first[:length]
        all_match = True
        for s in strs[1:]:
            if not isinstance(s, str) or not s.startswith(candidate):
                all_match = False
                break
        if all_match:
            prefix = candidate
        else:
            break
    return prefix