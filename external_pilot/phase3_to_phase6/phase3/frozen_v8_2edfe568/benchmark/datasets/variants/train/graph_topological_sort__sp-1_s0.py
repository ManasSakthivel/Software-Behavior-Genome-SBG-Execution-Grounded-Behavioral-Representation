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

class CycleError(Exception):
    """Raised when the graph contains a directed cycle."""

def _all_nodes(graph: dict) -> set:
    nodes = set(graph.keys())
    for neighbors in graph.values():
        nodes.update(neighbors)
    return nodes

def topological_sort_kahn(graph: Dict[Any, List[Any]]) -> List[Any]:
    """Topological sort via Kahn's algorithm (BFS in-degree reduction)."""
    nodes = _all_nodes(graph)
    in_degree = {num: 0 for num in nodes}
    for vertex in graph:
        for neighbor in graph[vertex]:
            in_degree[neighbor] += 1
    queue = deque((num for num in nodes if in_degree[num] == 0))
    order = []
    while queue:
        vertex = queue.popleft()
        order.append(vertex)
        for neighbor in graph.get(vertex, []):
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)
    if len(order) != len(nodes):
        raise CycleError('Graph contains a cycle — topological sort not possible')
    return order

def topological_sort_dfs(graph: Dict[Any, List[Any]]) -> List[Any]:
    """Topological sort via DFS (post-order reversal). Detects cycles."""
    nodes = _all_nodes(graph)
    (WHITE, GRAY, BLACK) = (0, 1, 2)
    color = {num: WHITE for num in nodes}
    output = []

    def dfs(u):
        color[u] = GRAY
        for v in graph.get(u, []):
            if color[v] == GRAY:
                raise CycleError(f'Back edge {u}→{v} detected — cycle exists')
            if color[v] == WHITE:
                dfs(v)
        color[u] = BLACK
        output.append(u)
    for vertex in nodes:
        if color[vertex] == WHITE:
            dfs(vertex)
    output.reverse()
    return output

def _is_valid_topo_order(order: list, graph: dict) -> bool:
    """Verify that order is a valid topological ordering."""
    pos = {vertex: idx for (idx, vertex) in enumerate(order)}
    for u in graph:
        for v in graph[u]:
            if pos[u] >= pos[v]:
                return False
    return True

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
        assert False, 'Should have raised CycleError'
    except CycleError:
        pass
    try:
        topological_sort_dfs(cyclic)
        assert False, 'Should have raised CycleError'
    except CycleError:
        pass
    assert topological_sort_kahn({}) == []
    assert topological_sort_dfs({}) == []
    chain = {'A': ['B'], 'B': ['C'], 'C': ['D'], 'D': []}
    order_chain_k = topological_sort_kahn(chain)
    assert order_chain_k == ['A', 'B', 'C', 'D']
    isolated = {'X': [], 'Y': [], 'Z': []}
    order_iso = topological_sort_kahn(isolated)
    assert set(order_iso) == {'X', 'Y', 'Z'}
    print('All topological_sort tests passed.')
if __name__ == '__main__':
    test_topological_sort()
    graph = {5: [2, 0], 4: [0, 1], 2: [3], 3: [1], 0: [], 1: []}
    print('Kahn order:', topological_sort_kahn(graph))
    print('DFS order: ', topological_sort_dfs(graph))