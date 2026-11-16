def fn_reverse_linked_list(node):
    prevnode = None
    while node:
        nextnode = node.successor
        node.successor = prevnode
        prevnode = node
        node = nextnode
    return prevnode
'\ndef reverse_linked_list(node):\n    prevnode = None\n    while node:\n        nextnode = node.successor\n        node.successor = prevnode\n        prevnode, node = node, nextnode\n    return prevnode\n\ndef reverse_linked_list(node):\n    prevnode = None\n    while node:\n        nextnode = node.successor\n        node.successor = prevnode\n        node, prevnode = nextnode, node\n    return prevnode\n\n'