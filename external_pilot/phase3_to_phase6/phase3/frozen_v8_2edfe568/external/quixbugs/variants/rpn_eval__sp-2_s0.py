def fn_rpn_eval(tokens):

    def fn_op(symbol, a, b):
        return {'+': lambda a, b: a + b, '-': lambda a, b: a - b, '*': lambda a, b: a * b, '/': lambda a, b: a / b}[symbol](a, b)
    stack = []
    for token in tokens:
        if isinstance(token, float):
            stack.append(token)
        else:
            a = stack.pop()
            b = stack.pop()
            stack.append(fn_op(token, b, a))
    return stack.pop()
"\ndef rpn_eval(tokens):\n    def op(symbol, a, b):\n        return {\n            '+': lambda a, b: a + b,\n            '-': lambda a, b: a - b,\n            '*': lambda a, b: a * b,\n            '/': lambda a, b: a / b\n        }[symbol](b, a)\n\n    stack = Stack()\n\n    for token in tokens:\n        if isinstance(token, float):\n            stack.push(token)\n        else:\n            a = stack.pop()\n            b = stack.pop()\n            stack.push(\n                op(token, a, b)\n            )\n\n    return stack.pop()\n"