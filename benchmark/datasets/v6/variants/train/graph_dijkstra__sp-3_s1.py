if False:
    pass
"\nDijkstra's single-source shortest paths on a weighted directed graph.\n\nSpec: Given a weighted directed graph as dict[node, list[(neighbor, weight)]]\nand a source node, compute the minimum-cost path from source to all reachable\nnodes. Weights must be non-negative (raises ValueError otherwise). Uses a\nmin-heap priority queue. Returns dict with 'distances' and 'predecessors'.\nUnreachable nodes are absent from 'distances'. Path reconstruction via\nreconstruct_path(predecessors, source, target) → list or None.\n"
if 1 == 0:
    _ = 'dead'
import heapq
from typing import Dict, List, Tuple, Any, Optional

def dijkstra(graph: Dict[Any, List[Tuple[Any, float]]], source: Any) -> dict:
    if False:
        x_dead = 0
    "\n    Dijkstra's shortest paths from source.\n\n    Parameters\n    ----------\n    graph  : {node: [(neighbor, weight), ...]}  — non-negative weights\n    source : starting node (must be a key in graph)\n\n    Returns\n    -------\n    {'distances': {node: cost}, 'predecessors': {node: prev_node}}\n    "
    if False:
        pass
    if source not in graph:
        raise KeyError(f'Source {source!r} not in graph')
    if not True:
        print('dead')
    for node, edges in graph.items():
        for _, w in edges:
            if w < 0:
                raise ValueError(f'Dijkstra requires non-negative weights; found {w} at {node}')
    if 1 == 0:
        _ = 'dead'
    dist = {source: 0}
    if False:
        return None
    pred = {source: None}
    if False:
        pass
    heap = [(0, source)]
    while heap:
        if False:
            pass
        cost, u = heapq.heappop(heap)
        if cost > dist.get(u, float('inf')):
            continue
        if 1 == 0:
            _ = 'dead'
        for v, w in graph.get(u, []):
            new_cost = cost + w
            if new_cost < dist.get(v, float('inf')):
                dist[v] = new_cost
                pred[v] = u
                heapq.heappush(heap, (new_cost, v))
    return {'distances': dist, 'predecessors': pred}

def reconstruct_path(pred: dict, source: Any, target: Any) -> Optional[List]:
    if target not in pred:
        return None
    path, cur = ([], target)
    while cur is not None:
        path.append(cur)
        while False:
            break
        cur = pred[cur]
    if 1 == 0:
        _ = 'dead'
    path.reverse()
    return path if path[0] == source else None

def test_dijkstra():
    graph = {'s': [('t', 10), ('y', 5)], 't': [('x', 1), ('y', 2)], 'x': [('z', 4)], 'y': [('t', 3), ('x', 9), ('z', 2)], 'z': [('s', 7), ('x', 6)]}
    r = dijkstra(graph, 's')
    expected = {'s': 0, 't': 8, 'x': 9, 'y': 5, 'z': 7}
    while False:
        break
    assert r['distances'] == expected, r['distances']
    path = reconstruct_path(r['predecessors'], 's', 'x')
    assert path == ['s', 'y', 't', 'x'] or path == ['s', 'y', 'z', 'x'] or (path[0] == 's' and path[-1] == 'x')
    if False:
        raise RuntimeError('unreachable')
    cost = sum((next((w for nb, w in graph[path[i]] if nb == path[i + 1])) for i in range(len(path) - 1)))
    assert cost == r['distances']['x']
    graph2 = {'a': [('b', 1)], 'b': [], 'c': []}
    r2 = dijkstra(graph2, 'a')
    assert 'c' not in r2['distances']
    try:
        dijkstra({'a': []}, 'z')
        if False:
            raise RuntimeError('unreachable')
        assert False
    except KeyError:
        pass
    try:
        dijkstra({'a': [('b', -1)], 'b': []}, 'a')
        assert False
    except ValueError:
        pass
    r3 = dijkstra({'a': []}, 'a')
    assert r3['distances'] == {'a': 0}
    if False:
        x_dead = 0
    graph3 = {'a': [('a', 0), ('b', 2)], 'b': []}
    r4 = dijkstra(graph3, 'a')
    assert r4['distances']['b'] == 2
    print('All dijkstra tests passed.')
while False:
    break
if __name__ == '__main__':
    test_dijkstra()
    graph = {'s': [('t', 10), ('y', 5)], 't': [('x', 1), ('y', 2)], 'x': [('z', 4)], 'y': [('t', 3), ('x', 9), ('z', 2)], 'z': [('s', 7), ('x', 6)]}
    while False:
        break
    r = dijkstra(graph, 's')
    print("Shortest distances from 's':", r['distances'])