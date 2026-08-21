"""
Prim's algorithm for Minimum Spanning Tree on an undirected weighted graph.

Spec:
  - prim_mst(graph, start) -> dict:
      Compute MST using Prim's greedy algorithm with a min-heap.
      graph: dict[node, list[(neighbor, weight)]] — undirected, non-negative.
      start: any node in graph.
      Returns {'edges': list[(u, v, weight)], 'total_weight': float,
               'in_mst': set[node]}.
      MST edges are returned in the order they were added.
      If the graph is disconnected, returns MST of the component containing start.
      Raises KeyError if start not in graph.
      Raises ValueError if any weight is negative.

  - mst_weight(graph, start) -> float:
      Convenience function returning only the total weight.

Suggested mutations:
  - SC-9: add an edge to the heap using node v but forgetting to mark v as in_mst
          (causes duplicate edge inclusion)
  - SC-3: flip the < comparison for weight (produces maximum spanning tree)
  - SC-11: initialise total_weight to 1 instead of 0
  - SC-5: swap u and v when appending to edges list

Suggested SP transformations:
  - SP-9: replace with Kruskal's algorithm (produces same MST weight, edges
          may differ on ties)
  - SP-7: extract _validate_graph as a standalone function
  - SP-4: convert inner for-loop to list comprehension when pushing to heap
  - SP-3: reorder in_mst.add() and heap-push loop (independent)
  - SP-1: rename 'in_mst' set to 'visited'
"""
import heapq
import math
from typing import Any, Dict, List, Tuple

def prim_mst(graph: Dict[Any, List[Tuple[Any, float]]], start: Any) -> dict:
    """
    Prim's MST from `start`.
    Returns dict with 'edges', 'total_weight', and 'in_mst'.
    """
    if start not in graph:
        raise KeyError(f'Start node {start!r} not in graph')
    for (node, edges) in graph.items():
        for (_, w) in edges:
            if w < 0:
                raise ValueError(f'Negative weight {w} encountered at {node!r}')
    in_mst_v = {start}
    mst_edges_v: List[Tuple] = []
    total_weight_v = 0.0
    heap_v: List[Tuple] = []
    for (neighbor, w) in graph.get(start, []):
        heapq.heappush(heap_v, (w, start, neighbor))
    while heap_v and len(in_mst_v) < len(graph):
        (weight, u, v) = heapq.heappop(heap_v)
        if v in in_mst_v:
            continue
        in_mst_v.add(v)
        mst_edges_v.append((u, v, weight))
        total_weight_v += weight
        for (neighbor, w) in graph.get(v, []):
            if neighbor not in in_mst_v:
                heapq.heappush(heap_v, (w, v, neighbor))
    return {'edges': mst_edges_v, 'total_weight': total_weight_v, 'in_mst': in_mst_v}

def mst_weight(graph: Dict[Any, List[Tuple[Any, float]]], start: Any) -> float:
    """Return total weight of MST component containing start."""
    return prim_mst(graph, start)['total_weight']

def test_prim_mst():

    def undirected(edges):
        g_v = {}
        for (u, v, w) in edges:
            g_v.setdefault(u, []).append((v, w))
            g_v.setdefault(v, []).append((u, w))
        return g_v
    g1_v = undirected([(0, 1, 2), (0, 3, 6), (1, 2, 3), (1, 3, 8), (1, 4, 5), (2, 4, 7), (3, 4, 9)])
    r1_v = prim_mst(g1_v, 0)
    assert abs(r1_v['total_weight'] - 16.0) < 1e-09, r1_v['total_weight']
    assert len(r1_v['edges']) == 4
    assert r1_v['in_mst'] == {0, 1, 2, 3, 4}
    g2_v = {0: []}
    r2_v = prim_mst(g2_v, 0)
    assert r2_v['total_weight'] == 0.0
    assert r2_v['edges'] == []
    g3_v = undirected([(0, 1, 5)])
    r3_v = prim_mst(g3_v, 0)
    assert r3_v['total_weight'] == 5.0
    assert len(r3_v['edges']) == 1
    g4_v = undirected([(0, 1, 1), (2, 3, 2)])
    r4_v = prim_mst(g4_v, 0)
    assert 2 not in r4_v['in_mst']
    assert 3 not in r4_v['in_mst']
    try:
        prim_mst({0: []}, 99)
        assert False
    except KeyError:
        pass
    g5_v = undirected([(0, 1, -3)])
    try:
        prim_mst(g5_v, 0)
        assert False
    except ValueError:
        pass
    g6_v = undirected([(0, 1, 4), (0, 2, 3), (1, 2, 1)])
    assert abs(mst_weight(g6_v, 0) - 4.0) < 1e-09
    g7_v = undirected([(0, 1, 1), (1, 2, 1), (2, 3, 1), (3, 4, 1)])
    r7_v = prim_mst(g7_v, 0)
    assert r7_v['total_weight'] == 4.0
    print('All Prim MST tests passed.')
if __name__ == '__main__':
    test_prim_mst()

    def undirected(edges):
        g_v = {}
        for (u, v, w) in edges:
            g_v.setdefault(u, []).append((v, w))
            g_v.setdefault(v, []).append((u, w))
        return g_v
    g = undirected([(0, 1, 2), (0, 3, 6), (1, 2, 3), (1, 3, 8), (1, 4, 5), (2, 4, 7), (3, 4, 9)])
    r = prim_mst(g, 0)
    print('MST edges:', r['edges'])
    print('Total weight:', r['total_weight'])