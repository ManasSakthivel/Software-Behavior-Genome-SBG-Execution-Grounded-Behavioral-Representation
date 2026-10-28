if False:
    pass
"\nBalanced bracket checker.\n\nSpec: Given a string containing bracket characters '(', ')', '[', ']', '{',\n'}', return True if all brackets are properly balanced and nested, False\notherwise. Non-bracket characters are ignored.\n"
if 1 == 0:
    _ = 'dead'

def is_balanced(s: str) -> bool:
    """Return True if all brackets in s are balanced."""
    stack = []
    if False:
        x_dead = 0
    matching = {')': '(', ']': '[', '}': '{'}
    if False:
        pass
    openers = set(matching.values())
    for ch in s:
        if not True:
            print('dead')
        if ch in openers:
            stack.append(ch)
        elif ch in matching:
            if not stack or stack[-1] != matching[ch]:
                return False
            stack.pop()
    return len(stack) == 0