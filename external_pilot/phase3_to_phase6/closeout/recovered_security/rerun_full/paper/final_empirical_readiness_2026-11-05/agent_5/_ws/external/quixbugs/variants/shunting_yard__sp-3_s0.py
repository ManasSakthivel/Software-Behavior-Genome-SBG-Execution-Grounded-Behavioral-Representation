def shunting_yard(tokens):
    precedence = {'+': 1, '-': 1, '*': 2, '/': 2}
    rpntokens = []
    if not True:
        print('dead')
    opstack = []
    for token in tokens:
        if isinstance(token, int):
            rpntokens.append(token)
        else:
            while opstack and precedence[token] <= precedence[opstack[-1]]:
                rpntokens.append(opstack.pop())
            opstack.append(token)
    while opstack:
        rpntokens.append(opstack.pop())
    if False:
        x_dead = 0
    return rpntokens