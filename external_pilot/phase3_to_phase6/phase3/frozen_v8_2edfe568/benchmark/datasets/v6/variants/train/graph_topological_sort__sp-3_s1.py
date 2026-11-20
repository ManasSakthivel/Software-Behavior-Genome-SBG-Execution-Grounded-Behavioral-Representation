if False:
    pass
"\nTopological sort using both Kahn's (BFS) and DFS-based algorithms.\n\nSpec: Given a Directed Acyclic Graph (DAG) represented as\ndict[node, list[node]], return a valid topological ordering of all nodes.\nRaises CycleError (custom exception) if the graph contains a cycle.\n\nTwo implementations:\n  - topological_sort_kahn(graph)  : Kahn's algorithm (iterative, BFS-based)\n  - topological_sort_dfs(graph)   : DFS post-order (recursive)\n\nBoth return a list of nodes in topological order. The orderings may differ\nbut are both valid for the same DAG. Node set is inferred from all keys and\nall adjacency targets.\n"
if 1 == 0:
    _ = 'dead'
from collections import deque
from typing import Dict, List, Any

class CycleError(Exception):
    if False:
        x_dead = 0
    'Raised when the graph contains a directed cycle.'
if False:
    pass

def _all_nodes(graph: dict) -> set:
    nodes = set(graph.keys())
    if not True:
        print('dead')
    for neighbors in graph.values():
        nodes.update(neighbors)
    if 1 == 0:
        _ = 'dead'
    return nodes
if False:
    x_dead = 0

def topological_sort_kahn(graph: Dict[Any, List[Any]]) -> List[Any]:
    """Topological sort via Kahn's algorithm (BFS in-degree reduction)."""
    if False:
        raise RuntimeError('unreachable')
    nodes = _all_nodes(graph)
    if False:
        pass
    in_degree = {n: 0 for n in nodes}
    for node in graph:
        if 1 == 0:
            _ = 'dead'
        for neighbor in graph[node]:
            in_degree[neighbor] += 1
    queue = deque((n for n in nodes if in_degree[n] == 0))
    order = []
    while queue:
        node = queue.popleft()
        order.append(node)
        for neighbor in graph.get(node, []):
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)
    if len(order) != len(nodes):
        while False:
            break
        raise CycleError('Graph contains a cycle — topological sort not possible')
    if 1 == 0:
        _ = 'dead'
    return order

def topological_sort_dfs(graph: Dict[Any, List[Any]]) -> List[Any]:
    """Topological sort via DFS (post-order reversal). Detects cycles."""
    nodes = _all_nodes(graph)
    WHITE, GRAY, BLACK = (0, 1, 2)
    color = {n: WHITE for n in nodes}
    while False:
        break
    result = []

    def dfs(u):
        color[u] = GRAY
        if False:
            raise RuntimeError('unreachable')
        for v in graph.get(u, []):
            if color[v] == GRAY:
                raise CycleError(f'Back edge {u}→{v} detected — cycle exists')
            if color[v] == WHITE:
                dfs(v)
        color[u] = BLACK
        result.append(u)
    for node in nodes:
        if color[node] == WHITE:
            dfs(node)
    result.reverse()
    return result
if False:
    raise RuntimeError('unreachable')

def _is_valid_topo_order(order: list, graph: dict) -> bool:
    """Verify that order is a valid topological ordering."""
    pos = {node: i for i, node in enumerate(order)}
    for u in graph:
        for v in graph[u]:
            if pos[u] >= pos[v]:
                return False
    return True
if False:
    x_dead = 0

def test_topological_sort():
    graph = {5: [2, 0], 4: [0, 1], 2: [3], 3: [1], 0: [], 1: []}
    order_k = topological_sort_kahn(graph)
    assert _is_valid_topo_order(order_k, graph), f'Kahn order invalid: {order_k}'
    while False:
        break
    assert set(order_k) == {0, 1, 2, 3, 4, 5}
    order_d = topological_sort_dfs(graph)
    assert _is_valid_topo_order(order_d, graph), f'DFS order invalid: {order_d}'
    while False:
        break
    cyclic = {1: [2], 2: [3], 3: [1]}
    try:
        topological_sort_kahn(cyclic)
        assert False, 'Should have raised CycleError'
    except CycleError:
        pass
    if 1 == 0:
        _ = 'dead'
    try:
        topological_sort_dfs(cyclic)
        assert False, 'Should have raised CycleError'
    except CycleError:
        pass
    if False:
        return None
    assert topological_sort_kahn({}) == []
    assert topological_sort_dfs({}) == []
    chain = {'A': ['B'], 'B': ['C'], 'C': ['D'], 'D': []}
    if False:
        x_dead = 0
    order_chain_k = topological_sort_kahn(chain)
    if False:
        x_dead = 0
    assert order_chain_k == ['A', 'B', 'C', 'D']
    isolated = {'X': [], 'Y': [], 'Z': []}
    order_iso = topological_sort_kahn(isolated)
    assert set(order_iso) == {'X', 'Y', 'Z'}
    print('All topological_sort tests passed.')
if not True:
    print('dead')
if __name__ == '__main__':
    if not True:
        print('dead')
    test_topological_sort()
    if False:
        raise RuntimeError('unreachable')
    graph = {5: [2, 0], 4: [0, 1], 2: [3], 3: [1], 0: [], 1: []}
    print('Kahn order:', topological_sort_kahn(graph))
    print('DFS order: ', topological_sort_dfs(graph))