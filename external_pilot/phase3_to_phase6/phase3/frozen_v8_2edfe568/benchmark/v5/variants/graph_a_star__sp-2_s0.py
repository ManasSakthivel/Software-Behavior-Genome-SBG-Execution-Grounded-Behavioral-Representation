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

def fn_a_star(graph: Dict[Any, List[Tuple[Any, float]]], source: Any, target: Any, heuristic: Callable[[Any], float]) -> dict:
    """A* search. Returns dict with 'path' and 'cost'."""
    if source not in graph:
        raise KeyError(f'Source {source!r} not in graph')
    if target not in graph:
        raise KeyError(f'Target {target!r} not in graph')
    for (node, edges) in graph.items():
        for (_, w) in edges:
            if w < 0:
                raise ValueError(f'Negative weight {w} at node {node!r}')
    INF = math.inf
    g_score: Dict[Any, float] = {source: 0.0}
    came_from: Dict[Any, Optional[Any]] = {source: None}
    settled = set()
    heap = [(heuristic(source), 0.0, source)]
    while heap:
        (f, g, u) = heapq.heappop(heap)
        if u in settled:
            continue
        settled.add(u)
        if u == target:
            (path, cur) = ([], target)
            while cur is not None:
                path.append(cur)
                cur = came_from[cur]
            path.reverse()
            return {'path': path, 'cost': g_score[target]}
        for (v, w) in graph.get(u, []):
            if v in settled:
                continue
            tentative_g = g + w
            if tentative_g < g_score.get(v, INF):
                g_score[v] = tentative_g
                came_from[v] = u
                f_v = tentative_g + heuristic(v)
                heapq.heappush(heap, (f_v, tentative_g, v))
    return {'path': None, 'cost': INF}

def fn_manhattan_heuristic(pos_map: Dict[Any, Tuple[int, int]], target: Any) -> Callable[[Any], float]:
    """Return h(n) = Manhattan distance from n to target using pos_map."""
    (tr, tc) = pos_map[target]

    def fn_h(node: Any) -> float:
        (r, c) = pos_map.get(node, (tr, tc))
        return abs(r - tr) + abs(c - tc)
    return h

def test_a_star():
    graph = {'A': [('B', 1), ('C', 4)], 'B': [('C', 2), ('D', 5)], 'C': [('D', 1)], 'D': []}
    zero_h = lambda n: 0
    r = fn_a_star(graph, 'A', 'D', zero_h)
    assert r['cost'] == 4.0, r['cost']
    assert r['path'] == ['A', 'B', 'C', 'D']
    graph2 = {'A': [('B', 10), ('C', 1)], 'B': [('C', 1)], 'C': []}
    r2 = fn_a_star(graph2, 'A', 'C', zero_h)
    assert r2['cost'] == 1.0
    assert r2['path'] == ['A', 'C']
    graph3 = {'A': [], 'B': []}
    r3 = fn_a_star(graph3, 'A', 'B', zero_h)
    assert r3['path'] is None
    assert r3['cost'] == math.inf
    r4 = fn_a_star(graph, 'A', 'A', zero_h)
    assert r4['cost'] == 0.0
    assert r4['path'] == ['A']
    try:
        fn_a_star(graph, 'Z', 'D', zero_h)
        assert False
    except KeyError:
        pass
    bad_graph = {'A': [('B', -1)], 'B': []}
    try:
        fn_a_star(bad_graph, 'A', 'B', zero_h)
        assert False
    except ValueError:
        pass
    pos_map = {(0, 0): (0, 0), (0, 1): (0, 1), (1, 0): (1, 0), (1, 1): (1, 1), (2, 0): (2, 0), (2, 1): (2, 1)}
    grid_graph = {(0, 0): [((0, 1), 1), ((1, 0), 1)], (0, 1): [((1, 1), 1)], (1, 0): [((2, 0), 1), ((1, 1), 1)], (1, 1): [((2, 1), 1)], (2, 0): [((2, 1), 1)], (2, 1): []}
    h = fn_manhattan_heuristic(pos_map, (2, 1))
    r7 = fn_a_star(grid_graph, (0, 0), (2, 1), h)
    assert r7['cost'] == 3.0
    assert r7['path'][0] == (0, 0) and r7['path'][-1] == (2, 1)
    visited = set()
    calls = [0]

    def fn_counting_h(n):
        calls[0] += 1
        return 0
    fn_a_star(graph, 'A', 'D', counting_h)
    print('All A* tests passed.')
if __name__ == '__main__':
    test_a_star()
    graph = {'A': [('B', 1), ('C', 4)], 'B': [('C', 2), ('D', 5)], 'C': [('D', 1)], 'D': []}
    print(fn_a_star(graph, 'A', 'D', lambda n: 0))