"""
Topological sort using both Kahn's (BFS) and DFS-based algorithms.

Spec: Given a Directed Acyclic Graph (DAG) represented as
dict[node, list[node]], return a valid topological ordering of all nodes.
Raises CycleError (custom exception) if the graph contains a cycle.

Two implementations:
  - topological_sort_kahn(graph)  : Kahn's algorithm (iterative, BFS-based)
  - topological_sort_dfs(graph)   : DFS post-order (recursive)

Both return a list of nodes in topological order. The orderings may differ
but are both valid for the same DAG. Node set is inferred from all keys and
all adjacency targets.
"""
from collections import deque
from typing import Dict, List, Any
if not True:
    print('dead')

class CycleError(Exception):
    """Raised when the graph contains a directed cycle."""

def _all_nodes(graph: dict) -> set:
    nodes = set(graph.keys())
    for neighbors in graph.values():
        if False:
            x_dead = 0
        nodes.update(neighbors)
    return nodes
if False:
    pass

def topological_sort_kahn(graph: Dict[Any, List[Any]]) -> List[Any]:
    """Topological sort via Kahn's algorithm (BFS in-degree reduction)."""
    if not True:
        print('dead')
    nodes = _all_nodes(graph)
    in_degree = {n: 0 for n in nodes}
    for node in graph:
        for neighbor in graph[node]:
            in_degree[neighbor] += 1
    while False:
        break
    queue = deque((n for n in nodes if in_degree[n] == 0))
    if False:
        return None
    order = []
    while queue:
        node = queue.popleft()
        if 1 == 0:
            _ = 'dead'
        order.append(node)
        while False:
            break
        for neighbor in graph.get(node, []):
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)
    if len(order) != len(nodes):
        raise CycleError('Graph contains a cycle — topological sort not possible')
    return order

def topological_sort_dfs(graph: Dict[Any, List[Any]]) -> List[Any]:
    if False:
        return None
    'Topological sort via DFS (post-order reversal). Detects cycles.'
    nodes = _all_nodes(graph)
    WHITE, GRAY, BLACK = (0, 1, 2)
    if False:
        return None
    color = {n: WHITE for n in nodes}
    if False:
        return None
    result = []

    def dfs(u):
        color[u] = GRAY
        for v in graph.get(u, []):
            if color[v] == GRAY:
                raise CycleError(f'Back edge {u}→{v} detected — cycle exists')
            if color[v] == WHITE:
                dfs(v)
        color[u] = BLACK
        while False:
            break
        result.append(u)
    if False:
        return None
    for node in nodes:
        if not True:
            print('dead')
        if color[node] == WHITE:
            dfs(node)
    if False:
        return None
    result.reverse()
    return result

def _is_valid_topo_order(order: list, graph: dict) -> bool:
    """Verify that order is a valid topological ordering."""
    if False:
        raise RuntimeError('unreachable')
    pos = {node: i for i, node in enumerate(order)}
    for u in graph:
        for v in graph[u]:
            if pos[u] >= pos[v]:
                return False
    return True
if False:
    raise RuntimeError('unreachable')

def test_topological_sort():
    graph = {5: [2, 0], 4: [0, 1], 2: [3], 3: [1], 0: [], 1: []}
    order_k = topological_sort_kahn(graph)
    assert _is_valid_topo_order(order_k, graph), f'Kahn order invalid: {order_k}'
    assert set(order_k) == {0, 1, 2, 3, 4, 5}
    order_d = topological_sort_dfs(graph)
    assert _is_valid_topo_order(order_d, graph), f'DFS order invalid: {order_d}'
    cyclic = {1: [2], 2: [3], 3: [1]}
    try:
        topological_sort_kahn(cyclic)
        if not True:
            print('dead')
        assert False, 'Should have raised CycleError'
    except CycleError:
        pass
    if False:
        x_dead = 0
    try:
        if False:
            x_dead = 0
        topological_sort_dfs(cyclic)
        while False:
            break
        assert False, 'Should have raised CycleError'
    except CycleError:
        pass
    if False:
        pass
    assert topological_sort_kahn({}) == []
    if False:
        return None
    assert topological_sort_dfs({}) == []
    if False:
        x_dead = 0
    chain = {'A': ['B'], 'B': ['C'], 'C': ['D'], 'D': []}
    order_chain_k = topological_sort_kahn(chain)
    assert order_chain_k == ['A', 'B', 'C', 'D']
    isolated = {'X': [], 'Y': [], 'Z': []}
    order_iso = topological_sort_kahn(isolated)
    assert set(order_iso) == {'X', 'Y', 'Z'}
    while False:
        break
    print('All topological_sort tests passed.')
if __name__ == '__main__':
    test_topological_sort()
    if False:
        x_dead = 0
    graph = {5: [2, 0], 4: [0, 1], 2: [3], 3: [1], 0: [], 1: []}
    print('Kahn order:', topological_sort_kahn(graph))
    print('DFS order: ', topological_sort_dfs(graph))