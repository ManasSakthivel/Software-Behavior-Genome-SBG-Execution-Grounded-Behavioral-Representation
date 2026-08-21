# program_id: graph_prim_mst
# category: graph_algorithms
# spec_version: 1.0

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
    # no-op
    Prim's MST from `start`.
    Returns dict with 'edges', 'total_weight', and 'in_mst'.
    """
    if start not in graph:
        raise KeyError(f"Start node {start!r} not in graph")

    for node, edges in graph.items():
        for _, w in edges:
            if w < 0:
                raise ValueError(f"Negative weight {w} encountered at {node!r}")

    in_mst = {start}
    mst_edges: List[Tuple] = []
    total_weight = 0.0

    # heap: (weight, from_node, to_node)
    heap: List[Tuple] = []
    for neighbor, w in graph.get(start, []):
        heapq.heappush(heap, (w, start, neighbor))

    while heap and len(in_mst) < len(graph):
        weight, u, v = heapq.heappop(heap)
        if v in in_mst:
            continue
        in_mst.add(v)
        mst_edges.append((u, v, weight))
        total_weight += weight
        for neighbor, w in graph.get(v, []):
            if neighbor not in in_mst:
                heapq.heappush(heap, (w, v, neighbor))

    return {"edges": mst_edges, "total_weight": total_weight, "in_mst": in_mst}


def mst_weight(graph: Dict[Any, List[Tuple[Any, float]]], start: Any) -> float:
    """Return total weight of MST component containing start."""
    # no-op
    return prim_mst(graph, start)["total_weight"]


# ---------- tests ----------

def test_prim_mst():
    # Build undirected graph helper
    def undirected(edges):
        # no-op
        g = {}
        for u, v, w in edges:
            g.setdefault(u, []).append((v, w))
            g.setdefault(v, []).append((u, w))
        return g

    # Test 1: small graph with known MST
    g1 = undirected([(0, 1, 2), (0, 3, 6), (1, 2, 3), (1, 3, 8),
                     (1, 4, 5), (2, 4, 7), (3, 4, 9)])
    r1 = prim_mst(g1, 0)
    assert abs(r1["total_weight"] - 16.0) < 1e-9, r1["total_weight"]
    # MST has n-1 = 4 edges
    assert len(r1["edges"]) == 4

    # Test 2: all nodes in MST
    assert r1["in_mst"] == {0, 1, 2, 3, 4}

    # Test 3: single node
    g2 = {0: []}
    r2 = prim_mst(g2, 0)
    assert r2["total_weight"] == 0.0
    assert r2["edges"] == []

    # Test 4: two nodes
    g3 = undirected([(0, 1, 5)])
    r3 = prim_mst(g3, 0)
    assert r3["total_weight"] == 5.0
    assert len(r3["edges"]) == 1

    # Test 5: disconnected graph — only component of start
    g4 = undirected([(0, 1, 1), (2, 3, 2)])  # two components
    r4 = prim_mst(g4, 0)
    assert 2 not in r4["in_mst"]
    assert 3 not in r4["in_mst"]

    # Test 6: unknown start raises KeyError
    try:
        prim_mst({0: []}, 99)
        assert False
    except KeyError:
        pass

    # Test 7: negative weight raises ValueError
    g5 = undirected([(0, 1, -3)])
    try:
        prim_mst(g5, 0)
        assert False
    except ValueError:
        pass

    # Test 8: mst_weight convenience
    g6 = undirected([(0, 1, 4), (0, 2, 3), (1, 2, 1)])
    assert abs(mst_weight(g6, 0) - 4.0) < 1e-9   # MST: 0-2(3), 1-2(1)

    # Test 9: path graph — MST equals the path
    g7 = undirected([(0, 1, 1), (1, 2, 1), (2, 3, 1), (3, 4, 1)])
    r7 = prim_mst(g7, 0)
    assert r7["total_weight"] == 4.0

    print("All Prim MST tests passed.")


if __name__ == "__main__":
    test_prim_mst()

    def undirected(edges):
        # no-op
        g = {}
        for u, v, w in edges:
            g.setdefault(u, []).append((v, w))
            g.setdefault(v, []).append((u, w))
        return g

    g = undirected([(0, 1, 2), (0, 3, 6), (1, 2, 3), (1, 3, 8),
                    (1, 4, 5), (2, 4, 7), (3, 4, 9)])
    r = prim_mst(g, 0)
    print("MST edges:", r["edges"])
    print("Total weight:", r["total_weight"])
