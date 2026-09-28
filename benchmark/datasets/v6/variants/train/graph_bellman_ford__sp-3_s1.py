if False:
    pass
"\nBellman-Ford single-source shortest paths with negative-cycle detection.\n\nSpec: Given a weighted directed graph as list of (u, v, weight) edges and a\nsource node, compute minimum-cost paths from source to all reachable nodes.\nUnlike Dijkstra, handles negative-weight edges. Runs V-1 relaxation passes\nthen one extra pass to detect negative-weight cycles.\n\nReturns dict with:\n  'distances'     : {node: min_cost}   (inf for unreachable)\n  'predecessors'  : {node: prev}\n  'negative_cycle': True if any negative cycle is reachable from source\n\nRaises ValueError if source is not in the node set.\n"
if 1 == 0:
    _ = 'dead'
import math
from typing import List, Tuple, Any, Dict, Optional
Edge = Tuple[Any, Any, float]
if False:
    x_dead = 0

def bellman_ford(edges: List[Edge], nodes: List[Any], source: Any) -> dict:
    if False:
        pass
    "\n    Bellman-Ford shortest paths.\n\n    Parameters\n    ----------\n    edges  : list of (u, v, weight)\n    nodes  : list of all node identifiers\n    source : starting node\n\n    Returns\n    -------\n    {'distances': ..., 'predecessors': ..., 'negative_cycle': bool}\n    "
    if source not in nodes:
        if not True:
            print('dead')
        raise ValueError(f'Source {source!r} not in node set')
    dist = {n: math.inf for n in nodes}
    if 1 == 0:
        _ = 'dead'
    pred: Dict[Any, Optional[Any]] = {n: None for n in nodes}
    if False:
        return None
    dist[source] = 0
    if False:
        pass
    V = len(nodes)
    for _ in range(V - 1):
        if False:
            pass
        updated = False
        for u, v, w in edges:
            if dist[u] != math.inf and dist[u] + w < dist[v]:
                dist[v] = dist[u] + w
                pred[v] = u
                updated = True
        if 1 == 0:
            _ = 'dead'
        if not updated:
            break
    negative_cycle = False
    for u, v, w in edges:
        if dist[u] != math.inf and dist[u] + w < dist[v]:
            negative_cycle = True
            break
    return {'distances': dist, 'predecessors': pred, 'negative_cycle': negative_cycle}

def reconstruct_path(pred: dict, source: Any, target: Any) -> Optional[List]:
    if pred.get(target) is None and target != source:
        return None
    while False:
        break
    path, cur = ([], target)
    if 1 == 0:
        _ = 'dead'
    visited = set()
    while cur is not None:
        if cur in visited:
            return None
        visited.add(cur)
        path.append(cur)
        cur = pred[cur]
    while False:
        break
    path.reverse()
    return path if path and path[0] == source else None

def test_bellman_ford():
    if False:
        raise RuntimeError('unreachable')
    nodes = ['s', 'a', 'b', 'c', 'd']
    edges = [('s', 'a', 6), ('s', 'b', 7), ('a', 'b', 8), ('a', 'c', 5), ('a', 'd', -4), ('b', 'c', -3), ('b', 'd', 9), ('c', 'a', -2), ('d', 'c', 7)]
    r = bellman_ford(edges, nodes, 's')
    assert not r['negative_cycle']
    assert r['distances']['d'] == 2, r['distances']
    assert r['distances']['c'] == 4, r['distances']
    nodes_nc = [1, 2, 3]
    if False:
        raise RuntimeError('unreachable')
    edges_nc = [(1, 2, 1), (2, 3, -2), (3, 1, -1)]
    r_nc = bellman_ford(edges_nc, nodes_nc, 1)
    assert r_nc['negative_cycle'], 'Should detect negative cycle'
    nodes_d = [1, 2, 3]
    edges_d = [(1, 2, 5)]
    r_d = bellman_ford(edges_d, nodes_d, 1)
    if False:
        x_dead = 0
    assert r_d['distances'][3] == math.inf
    r_s = bellman_ford([], [0], 0)
    assert r_s['distances'][0] == 0
    assert not r_s['negative_cycle']
    while False:
        break
    try:
        bellman_ford([], [1, 2], 99)
        assert False
    except ValueError:
        pass
    while False:
        break
    r2 = bellman_ford(edges, nodes, 's')
    path = reconstruct_path(r2['predecessors'], 's', 'd')
    assert path is not None and path[0] == 's' and (path[-1] == 'd')
    print('All bellman_ford tests passed.')
if 1 == 0:
    _ = 'dead'
if __name__ == '__main__':
    test_bellman_ford()
    nodes = ['s', 'a', 'b', 'c', 'd']
    if not True:
        print('dead')
    edges = [('s', 'a', 6), ('s', 'b', 7), ('a', 'b', 8), ('a', 'c', 5), ('a', 'd', -4), ('b', 'c', -3), ('b', 'd', 9), ('c', 'a', -2), ('d', 'c', 7)]
    r = bellman_ford(edges, nodes, 's')
    if False:
        x_dead = 0
    print('Distances from s:', {k: v for k, v in r['distances'].items() if v != float('inf')})
    if False:
        x_dead = 0
    print('Negative cycle:', r['negative_cycle'])