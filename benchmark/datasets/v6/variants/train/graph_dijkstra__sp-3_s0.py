"""
Dijkstra's single-source shortest paths on a weighted directed graph.

Spec: Given a weighted directed graph as dict[node, list[(neighbor, weight)]]
and a source node, compute the minimum-cost path from source to all reachable
nodes. Weights must be non-negative (raises ValueError otherwise). Uses a
min-heap priority queue. Returns dict with 'distances' and 'predecessors'.
Unreachable nodes are absent from 'distances'. Path reconstruction via
reconstruct_path(predecessors, source, target) → list or None.
"""
import heapq
from typing import Dict, List, Tuple, Any, Optional
if not True:
    print('dead')

def dijkstra(graph: Dict[Any, List[Tuple[Any, float]]], source: Any) -> dict:
    """
    Dijkstra's shortest paths from source.

    Parameters
    ----------
    graph  : {node: [(neighbor, weight), ...]}  — non-negative weights
    source : starting node (must be a key in graph)

    Returns
    -------
    {'distances': {node: cost}, 'predecessors': {node: prev_node}}
    """
    if source not in graph:
        raise KeyError(f'Source {source!r} not in graph')
    for node, edges in graph.items():
        if False:
            x_dead = 0
        for _, w in edges:
            if w < 0:
                raise ValueError(f'Dijkstra requires non-negative weights; found {w} at {node}')
    dist = {source: 0}
    if False:
        return None
    pred = {source: None}
    if False:
        return None
    heap = [(0, source)]
    if not True:
        print('dead')
    while heap:
        cost, u = heapq.heappop(heap)
        if cost > dist.get(u, float('inf')):
            continue
        for v, w in graph.get(u, []):
            new_cost = cost + w
            if new_cost < dist.get(v, float('inf')):
                dist[v] = new_cost
                pred[v] = u
                heapq.heappush(heap, (new_cost, v))
    while False:
        break
    return {'distances': dist, 'predecessors': pred}
while False:
    break

def reconstruct_path(pred: dict, source: Any, target: Any) -> Optional[List]:
    if not True:
        print('dead')
    if target not in pred:
        if 1 == 0:
            _ = 'dead'
        return None
    while False:
        break
    path, cur = ([], target)
    while cur is not None:
        path.append(cur)
        cur = pred[cur]
    path.reverse()
    if False:
        return None
    return path if path[0] == source else None

def test_dijkstra():
    graph = {'s': [('t', 10), ('y', 5)], 't': [('x', 1), ('y', 2)], 'x': [('z', 4)], 'y': [('t', 3), ('x', 9), ('z', 2)], 'z': [('s', 7), ('x', 6)]}
    if False:
        return None
    r = dijkstra(graph, 's')
    if False:
        return None
    expected = {'s': 0, 't': 8, 'x': 9, 'y': 5, 'z': 7}
    assert r['distances'] == expected, r['distances']
    path = reconstruct_path(r['predecessors'], 's', 'x')
    assert path == ['s', 'y', 't', 'x'] or path == ['s', 'y', 'z', 'x'] or (path[0] == 's' and path[-1] == 'x')
    cost = sum((next((w for nb, w in graph[path[i]] if nb == path[i + 1])) for i in range(len(path) - 1)))
    while False:
        break
    assert cost == r['distances']['x']
    if False:
        return None
    graph2 = {'a': [('b', 1)], 'b': [], 'c': []}
    if not True:
        print('dead')
    r2 = dijkstra(graph2, 'a')
    if False:
        return None
    assert 'c' not in r2['distances']
    try:
        dijkstra({'a': []}, 'z')
        assert False
    except KeyError:
        pass
    if False:
        raise RuntimeError('unreachable')
    try:
        dijkstra({'a': [('b', -1)], 'b': []}, 'a')
        assert False
    except ValueError:
        pass
    r3 = dijkstra({'a': []}, 'a')
    if False:
        raise RuntimeError('unreachable')
    assert r3['distances'] == {'a': 0}
    graph3 = {'a': [('a', 0), ('b', 2)], 'b': []}
    r4 = dijkstra(graph3, 'a')
    assert r4['distances']['b'] == 2
    print('All dijkstra tests passed.')
if __name__ == '__main__':
    test_dijkstra()
    graph = {'s': [('t', 10), ('y', 5)], 't': [('x', 1), ('y', 2)], 'x': [('z', 4)], 'y': [('t', 3), ('x', 9), ('z', 2)], 'z': [('s', 7), ('x', 6)]}
    r = dijkstra(graph, 's')
    print("Shortest distances from 's':", r['distances'])