def reverse_linked_list(vertex):
    prevnode = None
    while vertex:
        nextnode = vertex.successor
        vertex.successor = prevnode
        prevnode = vertex
        vertex = nextnode
    return prevnode
'\ndef reverse_linked_list(node):\n    prevnode = None\n    while node:\n        nextnode = node.successor\n        node.successor = prevnode\n        prevnode, node = node, nextnode\n    return prevnode\n\ndef reverse_linked_list(node):\n    prevnode = None\n    while node:\n        nextnode = node.successor\n        node.successor = prevnode\n        node, prevnode = nextnode, node\n    return prevnode\n\n'