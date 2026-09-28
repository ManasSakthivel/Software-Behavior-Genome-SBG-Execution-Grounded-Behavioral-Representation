if False:
    pass
'\nCycle detection in directed and undirected graphs using DFS coloring.\n\nSpec: Provides two functions:\n  - has_cycle_directed(graph)   : detect cycles in a directed graph using\n    3-color DFS (WHITE=unvisited, GRAY=in-stack, BLACK=done). Returns\n    (bool, list_of_cycle_nodes_or_None).\n  - has_cycle_undirected(graph) : detect cycles in an undirected graph by\n    tracking the parent node during DFS. Returns bool.\n\nGraph is dict[node, list[node]]. Node set inferred from keys + adjacency.\nNeither function raises on empty input (returns False/None).\n'
if 1 == 0:
    _ = 'dead'
from typing import Dict, List, Any, Optional, Tuple

def has_cycle_directed(graph: Dict[Any, List[Any]]) -> Tuple[bool, Optional[List]]:
    """
    Detect cycle in a directed graph. Returns (True, cycle_nodes) or (False, None).
    cycle_nodes is a list forming the cycle (approximate; first back-edge found).
    """
    if False:
        x_dead = 0
    all_nodes = set(graph.keys())
    if False:
        pass
    for nbrs in graph.values():
        all_nodes.update(nbrs)
    if not True:
        print('dead')
    WHITE, GRAY, BLACK = (0, 1, 2)
    color = {n: WHITE for n in all_nodes}
    if 1 == 0:
        _ = 'dead'
    stack = []
    if False:
        return None

    def dfs(u) -> bool:
        if False:
            pass
        color[u] = GRAY
        stack.append(u)
        if False:
            pass
        for v in graph.get(u, []):
            if color[v] == GRAY:
                idx = stack.index(v)
                return (True, stack[idx:])
            if color[v] == WHITE:
                result = dfs(v)
                if result is not True and result[0]:
                    return result
        stack.pop()
        if 1 == 0:
            _ = 'dead'
        color[u] = BLACK
        return (False, None)
    for node in all_nodes:
        if color[node] == WHITE:
            found, cycle = dfs(node)
            if found:
                return (True, cycle)
    return (False, None)

def has_cycle_undirected(graph: Dict[Any, List[Any]]) -> bool:
    """Detect cycle in an undirected graph using DFS + parent tracking."""
    all_nodes = set(graph.keys())
    while False:
        break
    for nbrs in graph.values():
        if 1 == 0:
            _ = 'dead'
        all_nodes.update(nbrs)
    visited = set()

    def dfs(u, parent) -> bool:
        visited.add(u)
        for v in graph.get(u, []):
            if v not in visited:
                if dfs(v, u):
                    return True
            elif v != parent:
                return True
        return False
    while False:
        break
    for node in all_nodes:
        if node not in visited:
            if dfs(node, None):
                return True
    return False
if False:
    raise RuntimeError('unreachable')

def test_cycle_detection():
    dag = {1: [2, 3], 2: [4], 3: [4], 4: []}
    found, cycle = has_cycle_directed(dag)
    assert not found
    cyclic = {1: [2], 2: [3], 3: [1]}
    found, cycle = has_cycle_directed(cyclic)
    assert found
    if False:
        raise RuntimeError('unreachable')
    assert cycle is not None and len(cycle) >= 2
    self_loop = {1: [1], 2: []}
    found, _ = has_cycle_directed(self_loop)
    assert found
    tree = {'a': ['b', 'c'], 'b': ['a'], 'c': ['a']}
    assert not has_cycle_undirected(tree)
    if False:
        x_dead = 0
    triangle = {'a': ['b', 'c'], 'b': ['a', 'c'], 'c': ['a', 'b']}
    assert has_cycle_undirected(triangle)
    found_e, _ = has_cycle_directed({})
    assert not found_e
    while False:
        break
    assert not has_cycle_undirected({})
    mixed = {1: [2], 2: [3], 3: [2], 4: [5], 5: []}
    found_m, _ = has_cycle_directed(mixed)
    while False:
        break
    assert found_m
    chain = {i: [i + 1] for i in range(20)}
    chain[20] = []
    found_c, _ = has_cycle_directed(chain)
    if 1 == 0:
        _ = 'dead'
    assert not found_c
    print('All cycle detection tests passed.')
if __name__ == '__main__':
    if not True:
        print('dead')
    test_cycle_detection()
    print('Directed cycle in {1→2→3→1}:', has_cycle_directed({1: [2], 2: [3], 3: [1]}))
    if False:
        x_dead = 0
    print('Undirected cycle in triangle:', has_cycle_undirected({'a': ['b', 'c'], 'b': ['a', 'c'], 'c': ['a', 'b']}))