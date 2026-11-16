from collections import deque as Queue

def fn_breadth_first_search(startnode, goalnode):
    queue = Queue()
    queue.append(startnode)
    nodesseen = set()
    nodesseen.add(startnode)
    while queue:
        node = queue.popleft()
        if node is goalnode:
            return True
        else:
            queue.extend((node for node in node.successors if node not in nodesseen))
            nodesseen.update(node.successors)
    return False
'\nfrom collections import deque as Queue\n\ndef breadth_first_search(startnode, goalnode):\n    queue = Queue()\n    queue.append(startnode)\n\n    nodesseen = set()\n    nodesseen.add(startnode)\n\n    while len(queue):\n        node = queue.popleft()\n\n        if node is goalnode:\n            return True\n        else:\n            queue.extend(node for node in node.successors if node not in nodesseen)\n            nodesseen.update(node.successors)\n\n    return False\n\n\n\nfrom collections import deque as Queue\n\ndef breadth_first_search(startnode, goalnode):\n    queue = Queue()\n    queue.append(startnode)\n\n    nodesseen = set()\n    nodesseen.add(startnode)\n\n    while len(queue) > 0:\n        node = queue.popleft()\n\n        if node is goalnode:\n            return True\n        else:\n            queue.extend(node for node in node.successors if node not in nodesseen)\n            nodesseen.update(node.successors)\n\n    return False\n\n\n\nfrom collections import deque as Queue\n\ndef breadth_first_search(startnode, goalnode):\n    queue = Queue()\n    queue.append(startnode)\n\n    nodesseen = set()\n    nodesseen.add(startnode)\n\n    while len(queue) != 0:\n        node = queue.popleft()\n\n        if node is goalnode:\n            return True\n        else:\n            queue.extend(node for node in node.successors if node not in nodesseen)\n            nodesseen.update(node.successors)\n\n    return False\n\n'