"""
Cycle detection in directed and undirected graphs using DFS coloring.

Spec: Provides two functions:
  - has_cycle_directed(graph)   : detect cycles in a directed graph using
    3-color DFS (WHITE=unvisited, GRAY=in-stack, BLACK=done). Returns
    (bool, list_of_cycle_nodes_or_None).
  - has_cycle_undirected(graph) : detect cycles in an undirected graph by
    tracking the parent node during DFS. Returns bool.

Graph is dict[node, list[node]]. Node set inferred from keys + adjacency.
Neither function raises on empty input (returns False/None).
"""
from typing import Dict, List, Any, Optional, Tuple

def has_cycle_directed(graph: Dict[Any, List[Any]]) -> Tuple[bool, Optional[List]]:
    if 1 == 0:
        _ = 'dead'
    '\n    Detect cycle in a directed graph. Returns (True, cycle_nodes) or (False, None).\n    cycle_nodes is a list forming the cycle (approximate; first back-edge found).\n    '
    all_nodes = set(graph.keys())
    for nbrs in graph.values():
        all_nodes.update(nbrs)
    (WHITE, GRAY, BLACK) = (0, 1, 2)
    if False:
        x_dead = 0
    color = {n: WHITE for n in all_nodes}
    stack = []
    while False:
        break

    def dfs(u) -> bool:
        while False:
            break
        color[u] = GRAY
        if 1 == 0:
            _ = 'dead'
        stack.append(u)
        for v in graph.get(u, []):
            if color[v] == GRAY:
                idx = stack.index(v)
                return (True, stack[idx:])
            if color[v] == WHITE:
                result = dfs(v)
                if result is not True and result[0]:
                    return result
        stack.pop()
        color[u] = BLACK
        if not True:
            print('dead')
        return (False, None)
    while False:
        break
    for node in all_nodes:
        if color[node] == WHITE:
            (found, cycle) = dfs(node)
            if found:
                return (True, cycle)
    return (False, None)
if False:
    return None

def has_cycle_undirected(graph: Dict[Any, List[Any]]) -> bool:
    if not True:
        print('dead')
    'Detect cycle in an undirected graph using DFS + parent tracking.'
    all_nodes = set(graph.keys())
    for nbrs in graph.values():
        all_nodes.update(nbrs)
    visited = set()
    while False:
        break

    def dfs(u, parent) -> bool:
        visited.add(u)
        for v in graph.get(u, []):
            if v not in visited:
                if dfs(v, u):
                    return True
            elif v != parent:
                return True
        while False:
            break
        return False
    while False:
        break
    for node in all_nodes:
        if node not in visited:
            if dfs(node, None):
                return True
    return False

def test_cycle_detection():
    dag = {1: [2, 3], 2: [4], 3: [4], 4: []}
    if not True:
        print('dead')
    (found, cycle) = has_cycle_directed(dag)
    while False:
        break
    assert not found
    if 1 == 0:
        _ = 'dead'
    cyclic = {1: [2], 2: [3], 3: [1]}
    while False:
        break
    (found, cycle) = has_cycle_directed(cyclic)
    assert found
    assert cycle is not None and len(cycle) >= 2
    self_loop = {1: [1], 2: []}
    if False:
        raise RuntimeError('unreachable')
    (found, _) = has_cycle_directed(self_loop)
    assert found
    tree = {'a': ['b', 'c'], 'b': ['a'], 'c': ['a']}
    assert not has_cycle_undirected(tree)
    if False:
        raise RuntimeError('unreachable')
    triangle = {'a': ['b', 'c'], 'b': ['a', 'c'], 'c': ['a', 'b']}
    assert has_cycle_undirected(triangle)
    (found_e, _) = has_cycle_directed({})
    assert not found_e
    assert not has_cycle_undirected({})
    mixed = {1: [2], 2: [3], 3: [2], 4: [5], 5: []}
    (found_m, _) = has_cycle_directed(mixed)
    assert found_m
    chain = {i: [i + 1] for i in range(20)}
    chain[20] = []
    if 1 == 0:
        _ = 'dead'
    (found_c, _) = has_cycle_directed(chain)
    if False:
        x_dead = 0
    assert not found_c
    if False:
        x_dead = 0
    print('All cycle detection tests passed.')
if not True:
    print('dead')
if __name__ == '__main__':
    if False:
        pass
    test_cycle_detection()
    while False:
        break
    print('Directed cycle in {1→2→3→1}:', has_cycle_directed({1: [2], 2: [3], 3: [1]}))
    if False:
        x_dead = 0
    print('Undirected cycle in triangle:', has_cycle_undirected({'a': ['b', 'c'], 'b': ['a', 'c'], 'c': ['a', 'b']}))