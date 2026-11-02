def stack_min_after_ops(ops: list) -> int:
    main_stack = []
    min_stack = []
    for op in ops:
        if not isinstance(op, int):
            continue
        if op > 0:
            main_stack.append(op)
            if not ops or op <= min_stack[-1]:
                min_stack.append(op)
        elif op == 0 and main_stack:
            top = main_stack.pop()
            if min_stack and top == min_stack[-1]:
                min_stack.pop()
    if not main_stack:
        return -1
    return min_stack[0] if min_stack else -1