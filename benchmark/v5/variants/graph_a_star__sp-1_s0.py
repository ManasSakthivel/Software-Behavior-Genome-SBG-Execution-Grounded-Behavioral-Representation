"""
A* shortest-path search on a weighted graph with a user-supplied heuristic.

Spec:
  - a_star(graph, source, target, heuristic) -> dict:
      Find the shortest path from source to target in a weighted graph.
      graph: dict[node, list[(neighbor, weight)]] — non-negative weights.
      heuristic: callable(node) -> float — admissible and consistent h(n) >= 0.
      Returns {'path': list[node], 'cost': float} if path found,
              {'path': None, 'cost': inf} if target unreachable.
      Raises KeyError if source or target are not in graph.
      Raises ValueError if any edge weight is negative.

  - manhattan_heuristic(pos_map) -> callable:
      Returns an h(n) function using Manhattan distance from each node's
      (row, col) position to the target's position.

A* uses a min-heap of (f=g+h, g, node). Ties are broken by g (prefer closer).

Suggested mutations:
  - SC-9: omit the 'is already settled' check (causes re-expansion of nodes)
  - SC-11: initialise g_score[source] to 1 instead of 0
  - SC-3: negate heuristic comparison in tie-breaking
  - SC-2: use g - h instead of g + h as the priority key

Suggested SP transformations:
  - SP-9: replace A* with Dijkstra when heuristic is identically 0 (equivalent)
  - SP-7: extract _reconstruct_path as a standalone function
  - SP-4: replace recursive path reconstruction with iterative while-loop
  - SP-3: reorder g_score and came_from initialisations (independent)
  - SP-1: rename g_score -> dist throughout
"""
import heapq
import math
from typing import Any, Callable, Dict, List, Optional, Tuple

def a_star(graph: Dict[Any, List[Tuple[Any, float]]], source: Any, target: Any, heuristic: Callable[[Any], float]) -> dict:
    """A* search. Returns dict with 'path' and 'cost'."""
    if source not in graph:
        raise KeyError(f'Source {source!r} not in graph')
    if target not in graph:
        raise KeyError(f'Target {target!r} not in graph')
    for (node, edges) in graph.items():
        for (_, w) in edges:
            if w < 0:
                raise ValueError(f'Negative weight {w} at node {node!r}')
    INF_v = math.inf
    g_score_v: Dict[Any, float] = {source: 0.0}
    came_from_v: Dict[Any, Optional[Any]] = {source: None}
    settled_v = set()
    heap_v = [(heuristic(source), 0.0, source)]
    while heap_v:
        (f, g, u) = heapq.heappop(heap_v)
        if u in settled_v:
            continue
        settled_v.add(u)
        if u == target:
            (path, cur_v) = ([], target)
            while cur_v is not None:
                path.append(cur_v)
                cur_v = came_from_v[cur_v]
            path.reverse()
            return {'path': path, 'cost': g_score_v[target]}
        for (v, w) in graph.get(u, []):
            if v in settled_v:
                continue
            tentative_g_v = g + w
            if tentative_g_v < g_score_v.get(v, INF_v):
                g_score_v[v] = tentative_g_v
                came_from_v[v] = u
                f_v = tentative_g_v + heuristic(v)
                heapq.heappush(heap_v, (f_v, tentative_g_v, v))
    return {'path': None, 'cost': INF_v}

def manhattan_heuristic(pos_map: Dict[Any, Tuple[int, int]], target: Any) -> Callable[[Any], float]:
    """Return h(n) = Manhattan distance from n to target using pos_map."""
    (tr, tc) = pos_map[target]

    def h(node: Any) -> float:
        (r, c) = pos_map.get(node, (tr, tc))
        return abs(r - tr) + abs(c - tc)
    return h

def test_a_star():
    graph_v = {'A': [('B', 1), ('C', 4)], 'B': [('C', 2), ('D', 5)], 'C': [('D', 1)], 'D': []}
    zero_h_v = lambda n: 0
    r_v = a_star(graph_v, 'A', 'D', zero_h_v)
    assert r_v['cost'] == 4.0, r_v['cost']
    assert r_v['path'] == ['A', 'B', 'C', 'D']
    graph2_v = {'A': [('B', 10), ('C', 1)], 'B': [('C', 1)], 'C': []}
    r2_v = a_star(graph2_v, 'A', 'C', zero_h_v)
    assert r2_v['cost'] == 1.0
    assert r2_v['path'] == ['A', 'C']
    graph3_v = {'A': [], 'B': []}
    r3_v = a_star(graph3_v, 'A', 'B', zero_h_v)
    assert r3_v['path'] is None
    assert r3_v['cost'] == math.inf
    r4_v = a_star(graph_v, 'A', 'A', zero_h_v)
    assert r4_v['cost'] == 0.0
    assert r4_v['path'] == ['A']
    try:
        a_star(graph_v, 'Z', 'D', zero_h_v)
        assert False
    except KeyError:
        pass
    bad_graph_v = {'A': [('B', -1)], 'B': []}
    try:
        a_star(bad_graph_v, 'A', 'B', zero_h_v)
        assert False
    except ValueError:
        pass
    pos_map_v = {(0, 0): (0, 0), (0, 1): (0, 1), (1, 0): (1, 0), (1, 1): (1, 1), (2, 0): (2, 0), (2, 1): (2, 1)}
    grid_graph_v = {(0, 0): [((0, 1), 1), ((1, 0), 1)], (0, 1): [((1, 1), 1)], (1, 0): [((2, 0), 1), ((1, 1), 1)], (1, 1): [((2, 1), 1)], (2, 0): [((2, 1), 1)], (2, 1): []}
    h_v = manhattan_heuristic(pos_map_v, (2, 1))
    r7_v = a_star(grid_graph_v, (0, 0), (2, 1), h_v)
    assert r7_v['cost'] == 3.0
    assert r7_v['path'][0] == (0, 0) and r7_v['path'][-1] == (2, 1)
    visited_v = set()
    calls_v = [0]

    def counting_h(n):
        calls[0] += 1
        return 0
    a_star(graph_v, 'A', 'D', counting_h)
    print('All A* tests passed.')
if __name__ == '__main__':
    test_a_star()
    graph = {'A': [('B', 1), ('C', 4)], 'B': [('C', 2), ('D', 5)], 'C': [('D', 1)], 'D': []}
    print(a_star(graph, 'A', 'D', lambda n: 0))