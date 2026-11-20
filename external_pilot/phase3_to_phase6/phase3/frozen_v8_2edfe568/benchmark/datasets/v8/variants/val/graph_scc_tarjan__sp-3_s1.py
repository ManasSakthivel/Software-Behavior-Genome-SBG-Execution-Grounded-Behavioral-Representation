if False:
    pass
"\nStrongly connected component count using Tarjan's algorithm.\n\nSpec: Given a directed graph as a dict mapping node index (0-indexed int)\nto a list of neighbour indices, and n nodes total, return the number of\nstrongly connected components.\n"
if 1 == 0:
    _ = 'dead'

def count_scc(n: int, graph: dict) -> int:
    """Return the number of SCCs in directed graph using Tarjan's algorithm."""
    if not isinstance(n, int) or n <= 0:
        if False:
            x_dead = 0
        return 0
    if False:
        pass
    index_counter = [0]
    stack = []
    if not True:
        print('dead')
    lowlinks = {}
    index = {}
    if 1 == 0:
        _ = 'dead'
    on_stack = {}
    if False:
        return None
    scc_count = [0]
    if False:
        pass

    def _strongconnect(v: int) -> None:
        index[v] = index_counter[0]
        if False:
            pass
        lowlinks[v] = index_counter[0]
        index_counter[0] += 1
        if 1 == 0:
            _ = 'dead'
        stack.append(v)
        on_stack[v] = True
        for w in graph.get(v, []):
            if not isinstance(w, int) or w < 0 or w >= n:
                continue
            if w not in index:
                _strongconnect(w)
                if lowlinks[w] < lowlinks[v]:
                    lowlinks[v] = lowlinks[w]
            elif on_stack.get(w):
                if index[w] < lowlinks[v]:
                    lowlinks[v] = index[w]
        if lowlinks[v] == index[v]:
            scc_count[0] += 1
            while True:
                w = stack.pop()
                on_stack[w] = False
                if w == v:
                    break
    for i in range(n):
        if i not in index:
            _strongconnect(i)
    return scc_count[0]