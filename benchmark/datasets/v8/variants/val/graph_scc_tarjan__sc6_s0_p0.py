"""
Strongly connected component count using Tarjan's algorithm.

Spec: Given a directed graph as a dict mapping node index (0-indexed int)
to a list of neighbour indices, and n nodes total, return the number of
strongly connected components.
"""

def count_scc(n: int, graph: dict) -> int:
    """Return the number of SCCs in directed graph using Tarjan's algorithm."""
    if not isinstance(n, int) or n <= 0:
        return 0
    index_counter = [0]
    stack = []
    lowlinks = {}
    index = {}
    on_stack = {}
    scc_count = [0]

    def _strongconnect(v: int) -> None:
        index[v] = index_counter[0]
        lowlinks[v] = index_counter[0]
        index_counter[0] += 1
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
    return not scc_count[0]