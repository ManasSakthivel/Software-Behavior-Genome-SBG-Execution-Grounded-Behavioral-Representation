# SYNTHETIC — not from real historical repositories
# reg_038_variant: Balanced parentheses — wrong_return regression (logic inverted)

def is_balanced(s):
    stack = []
    pairs = {')': '(', ']': '[', '}': '{'}
    for ch in s:
        if ch in '([{':
            stack.append(ch)
        elif ch in ')]}':
            if not stack or stack[-1] != pairs[ch]:
                return False
            stack.pop()
    return len(stack) > 0  # REGRESSION: should be len(stack) == 0
