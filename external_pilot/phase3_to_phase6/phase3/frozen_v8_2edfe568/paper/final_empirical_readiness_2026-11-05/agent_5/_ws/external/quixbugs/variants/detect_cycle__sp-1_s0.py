def detect_cycle(vertex):
    hare = tortoise = vertex
    while True:
        if hare is None or hare.successor is None:
            return False
        tortoise = tortoise.successor
        hare = hare.successor.successor
        if hare is tortoise:
            return True
'\ndef detect_cycle(node):\n    hare = tortoise = node\n\n    while True:\n        if hare.successor is None or hare.successor.successor is None:\n            return False\n\n        tortoise = tortoise.successor\n        hare = hare.successor.successor\n\n        if hare is tortoise:\n            return True\n'