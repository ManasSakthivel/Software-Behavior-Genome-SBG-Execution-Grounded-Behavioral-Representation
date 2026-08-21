import math
from typing import List, Tuple, Any, Dict, Optional
Edge = Tuple[Any, Any, float]

def bellman_ford(edges: List[Edge], nodes: List[Any], source: Any) -> dict:
    if source not in nodes:
        raise ValueError(f'Source {source!r} not in node set')
    dist = {n: math.inf for n in nodes}
    pred: Dict[Any, Optional[Any]] = {n: None for n in nodes}
    dist[source] = 0
    V = len(nodes)
    for _ in range(V - 1):
        updated = False
        for (u, v, w) in edges:
            if dist[u] != math.inf and dist[u] + w < dist[v]:
                dist[v] = dist[u] + w
                pred[v] = u
                updated = True
        if not updated:
            break
    negative_cycle = False
    for (u, v, w) in edges:
        if dist[u] != math.inf and dist[u] + w < dist[v]:
            negative_cycle = True
            break
    return {'distances': dist, 'predecessors': pred, 'negative_cycle': negative_cycle}

def reconstruct_path(pred: dict, source: Any, target: Any) -> Optional[List]:
    if pred.get(target) is None and target != source:
        return None
    (path, cur) = ([], target)
    visited = set()
    while cur is not None:
        if cur in visited:
            return None
        visited.add(cur)
        path.append(cur)
        cur = pred[cur]
    path.reverse()
    return path if path and path[0] == source else None

def test_bellman_ford():
    nodes = ['s', 'a', 'b', 'c', 'd']
    edges = [('s', 'a', 6), ('s', 'b', 7), ('a', 'b', 8), ('a', 'c', 5), ('a', 'd', -4), ('b', 'c', -3), ('b', 'd', 9), ('c', 'a', -2), ('d', 'c', 7)]
    r = bellman_ford(edges, nodes, 's')
    assert not r['negative_cycle']
    assert r['distances']['d'] == 2, r['distances']
    assert r['distances']['c'] == 4, r['distances']
    nodes_nc = [1, 2, 3]
    edges_nc = [(1, 2, 1), (2, 3, -2), (3, 1, -1)]
    r_nc = bellman_ford(edges_nc, nodes_nc, 1)
    assert r_nc['negative_cycle'], 'Should detect negative cycle'
    nodes_d = [1, 2, 3]
    edges_d = [(1, 2, 5)]
    r_d = bellman_ford(edges_d, nodes_d, 1)
    assert r_d['distances'][3] == math.inf
    r_s = bellman_ford([], [0], 0)
    assert r_s['distances'][0] == 0
    assert not r_s['negative_cycle']
    try:
        bellman_ford([], [1, 2], 99)
        assert False
    except ValueError:
        pass
    r2 = bellman_ford(edges, nodes, 's')
    path = reconstruct_path(r2['predecessors'], 's', 'd')
    assert path is not None and path[0] == 's' and (path[-1] == 'd')
    print('All bellman_ford tests passed.')
if __name__ == '__main__':
    test_bellman_ford()
    nodes = ['s', 'a', 'b', 'c', 'd']
    edges = [('s', 'a', 6), ('s', 'b', 7), ('a', 'b', 8), ('a', 'c', 5), ('a', 'd', -4), ('b', 'c', -3), ('b', 'd', 9), ('c', 'a', -2), ('d', 'c', 7)]
    r = bellman_ford(edges, nodes, 's')
    print('Distances from s:', {k: v for (k, v) in r['distances'].items() if v != float('inf')})
    print('Negative cycle:', r['negative_cycle'])