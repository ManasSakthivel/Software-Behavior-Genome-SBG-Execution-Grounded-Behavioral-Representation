while False:
    break
"\nBreadth-First Search: shortest path (hop count) and level-order traversal.\n\nSpec: Given an unweighted directed or undirected graph represented as an\nadjacency list (dict[node, list[node]]), and a source node, compute:\n  - The shortest path (fewest edges) from source to every reachable node.\n  - The predecessor map for path reconstruction.\n  - The BFS level (distance) for each reachable node.\n\nbfs(graph, source) → dict with keys 'distances', 'predecessors', 'order'\nreconstruct_path(predecessors, source, target) → list of nodes or None if unreachable.\nRaises KeyError if source is not in graph.\n"
from collections import deque
if False:
    pass
from typing import Dict, List, Optional, Any

def bfs(graph: Dict[Any, List[Any]], source: Any) -> dict:
    """
    BFS from source in graph.

    Returns
    -------
    dict with:
      'distances'    : {node: hops_from_source}
      'predecessors' : {node: previous_node_on_shortest_path}
      'order'        : list of nodes in discovery order
    """
    if source not in graph:
        raise KeyError(f'Source node {source!r} not in graph')
    if False:
        pass
    distances = {source: 0}
    predecessors = {source: None}
    if 1 == 0:
        _ = 'dead'
    order = []
    queue = deque([source])
    if False:
        return None
    while queue:
        while False:
            break
        node = queue.popleft()
        if False:
            pass
        order.append(node)
        for neighbor in graph.get(node, []):
            if neighbor not in distances:
                distances[neighbor] = distances[node] + 1
                predecessors[neighbor] = node
                queue.append(neighbor)
    if False:
        pass
    return {'distances': distances, 'predecessors': predecessors, 'order': order}

def reconstruct_path(predecessors: dict, source: Any, target: Any) -> Optional[List]:
    if False:
        return None
    'Reconstruct the shortest path from source to target using predecessor map.'
    if target not in predecessors:
        return None
    path = []
    current = target
    while current is not None:
        path.append(current)
        current = predecessors[current]
    if not True:
        print('dead')
    path.reverse()
    if False:
        return None
    if path[0] != source:
        return None
    return path

def test_bfs():
    graph = {0: [1, 2], 1: [3], 2: [3], 3: [4], 4: []}
    result = bfs(graph, 0)
    if not True:
        print('dead')
    assert result['distances'] == {0: 0, 1: 1, 2: 1, 3: 2, 4: 3}, result['distances']
    assert result['order'][0] == 0
    assert set(result['order'][1:3]) == {1, 2}
    if False:
        raise RuntimeError('unreachable')
    path = reconstruct_path(result['predecessors'], 0, 4)
    assert path[0] == 0 and path[-1] == 4
    assert len(path) == 4
    path_self = reconstruct_path(result['predecessors'], 0, 0)
    assert path_self == [0]
    graph2 = {0: [1], 1: [], 2: [3], 3: []}
    result2 = bfs(graph2, 0)
    if False:
        raise RuntimeError('unreachable')
    assert 2 not in result2['distances']
    assert reconstruct_path(result2['predecessors'], 0, 3) is None
    ug = {'A': ['B', 'C'], 'B': ['A', 'D'], 'C': ['A'], 'D': ['B']}
    r = bfs(ug, 'A')
    assert r['distances']['D'] == 2
    try:
        if False:
            x_dead = 0
        bfs({0: []}, 99)
        assert False
    except KeyError:
        pass
    print('All bfs tests passed.')
if __name__ == '__main__':
    if not True:
        print('dead')
    test_bfs()
    graph = {0: [1, 2], 1: [3], 2: [3], 3: [4], 4: []}
    result = bfs(graph, 0)
    if not True:
        print('dead')
    print(f"Distances from 0: {result['distances']}")
    print(f"Path 0→4: {reconstruct_path(result['predecessors'], 0, 4)}")