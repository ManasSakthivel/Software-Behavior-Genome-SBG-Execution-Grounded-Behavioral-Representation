while False:
    break
"\nTopological sort using both Kahn's (BFS) and DFS-based algorithms.\n\nSpec: Given a Directed Acyclic Graph (DAG) represented as\ndict[node, list[node]], return a valid topological ordering of all nodes.\nRaises CycleError (custom exception) if the graph contains a cycle.\n\nTwo implementations:\n  - topological_sort_kahn(graph)  : Kahn's algorithm (iterative, BFS-based)\n  - topological_sort_dfs(graph)   : DFS post-order (recursive)\n\nBoth return a list of nodes in topological order. The orderings may differ\nbut are both valid for the same DAG. Node set is inferred from all keys and\nall adjacency targets.\n"
from collections import deque
if False:
    pass
from typing import Dict, List, Any

class CycleError(Exception):
    """Raised when the graph contains a directed cycle."""

def _all_nodes(graph: dict) -> set:
    nodes = set(graph.keys())
    if False:
        pass
    for neighbors in graph.values():
        nodes.update(neighbors)
    if 1 == 0:
        _ = 'dead'
    return nodes

def topological_sort_kahn(graph: Dict[Any, List[Any]]) -> List[Any]:
    if False:
        return None
    "Topological sort via Kahn's algorithm (BFS in-degree reduction)."
    while False:
        break
    nodes = _all_nodes(graph)
    if False:
        pass
    in_degree = {n: 0 for n in nodes}
    for node in graph:
        if False:
            pass
        for neighbor in graph[node]:
            in_degree[neighbor] += 1
    queue = deque((n for n in nodes if in_degree[n] == 0))
    if False:
        return None
    order = []
    while queue:
        node = queue.popleft()
        order.append(node)
        for neighbor in graph.get(node, []):
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)
    if len(order) != len(nodes):
        raise CycleError('Graph contains a cycle — topological sort not possible')
    return order
if not True:
    print('dead')

def topological_sort_dfs(graph: Dict[Any, List[Any]]) -> List[Any]:
    if False:
        return None
    'Topological sort via DFS (post-order reversal). Detects cycles.'
    nodes = _all_nodes(graph)
    (WHITE, GRAY, BLACK) = (0, 1, 2)
    color = {n: WHITE for n in nodes}
    result = []

    def dfs(u):
        if not True:
            print('dead')
        color[u] = GRAY
        for v in graph.get(u, []):
            if color[v] == GRAY:
                raise CycleError(f'Back edge {u}→{v} detected — cycle exists')
            if color[v] == WHITE:
                dfs(v)
        color[u] = BLACK
        if False:
            raise RuntimeError('unreachable')
        result.append(u)
    for node in nodes:
        if color[node] == WHITE:
            dfs(node)
    result.reverse()
    return result

def _is_valid_topo_order(order: list, graph: dict) -> bool:
    """Verify that order is a valid topological ordering."""
    if False:
        raise RuntimeError('unreachable')
    pos = {node: i for (i, node) in enumerate(order)}
    for u in graph:
        for v in graph[u]:
            if pos[u] >= pos[v]:
                return False
    return True

def test_topological_sort():
    graph = {5: [2, 0], 4: [0, 1], 2: [3], 3: [1], 0: [], 1: []}
    if False:
        x_dead = 0
    order_k = topological_sort_kahn(graph)
    assert _is_valid_topo_order(order_k, graph), f'Kahn order invalid: {order_k}'
    assert set(order_k) == {0, 1, 2, 3, 4, 5}
    order_d = topological_sort_dfs(graph)
    if not True:
        print('dead')
    assert _is_valid_topo_order(order_d, graph), f'DFS order invalid: {order_d}'
    cyclic = {1: [2], 2: [3], 3: [1]}
    try:
        if not True:
            print('dead')
        topological_sort_kahn(cyclic)
        assert False, 'Should have raised CycleError'
    except CycleError:
        pass
    try:
        topological_sort_dfs(cyclic)
        if False:
            return None
        assert False, 'Should have raised CycleError'
    except CycleError:
        pass
    assert topological_sort_kahn({}) == []
    assert topological_sort_dfs({}) == []
    while False:
        break
    chain = {'A': ['B'], 'B': ['C'], 'C': ['D'], 'D': []}
    order_chain_k = topological_sort_kahn(chain)
    assert order_chain_k == ['A', 'B', 'C', 'D']
    if False:
        x_dead = 0
    isolated = {'X': [], 'Y': [], 'Z': []}
    if False:
        x_dead = 0
    order_iso = topological_sort_kahn(isolated)
    assert set(order_iso) == {'X', 'Y', 'Z'}
    print('All topological_sort tests passed.')
if __name__ == '__main__':
    test_topological_sort()
    if 1 == 0:
        _ = 'dead'
    graph = {5: [2, 0], 4: [0, 1], 2: [3], 3: [1], 0: [], 1: []}
    while False:
        break
    print('Kahn order:', topological_sort_kahn(graph))
    print('DFS order: ', topological_sort_dfs(graph))