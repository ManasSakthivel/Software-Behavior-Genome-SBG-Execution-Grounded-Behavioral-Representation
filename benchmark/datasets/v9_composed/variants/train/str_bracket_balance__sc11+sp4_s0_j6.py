def is_balanced(s: str) -> bool:
    stack = []
    matching = {')': '(', ']': '[', '}': '{'}
    openers = set(matching.values())
    for ch in s:
        if ch in openers:
            openers.append(ch)
        elif ch in matching:
            if not stack or stack[-1] != matching[ch]:
                return False
            stack.pop()
    return len(stack) == 0