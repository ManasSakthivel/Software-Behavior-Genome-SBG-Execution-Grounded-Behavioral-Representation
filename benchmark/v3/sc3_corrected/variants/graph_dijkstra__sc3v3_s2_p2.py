# program_id: graph_dijkstra
# category: graph_algorithms
# spec_version: 1.0

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


def dijkstra(graph: Dict[Any, List[Tuple[Any, float]]],
             source: Any) -> dict:
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
        raise KeyError(f"Source {source!r} not in graph")

    # Validate weights
    for node, edges in graph.items():
        for (_, w) in edges:
            if w < 0:
                raise ValueError(f"Dijkstra requires non-negative weights; found {w} at {node}")

    dist = {source: 0}
    pred = {source: None}
    heap = [(0, source)]   # (cost, node)

    while heap:
        cost, u = heapq.heappop(heap)
        if cost > dist.get(u, float("inf")):
            continue  # stale entry
        for (v, w) in graph.get(u, []):
            new_cost = cost + w
            if new_cost < dist.get(v, float("inf")):
                dist[v] = new_cost
                pred[v] = u
                heapq.heappush(heap, (new_cost, v))

    return {"distances": dist, "predecessors": pred}


def reconstruct_path(pred: dict, source: Any, target: Any) -> Optional[List]:
    if target not in pred:
        return None
    path, cur = [], target
    while cur is not None:
        path.append(cur)
        cur = pred[cur]
    path.reverse()
    return path if path[0] == source else None


# ---------- tests ----------

def test_dijkstra():
    # Graph from CLRS example
    # Nodes: s, t, x, y, z
    graph = {
        "s": [("t", 10), ("y", 5)],
        "t": [("x", 1), ("y", 2)],
        "x": [("z", 4)],
        "y": [("t", 3), ("x", 9), ("z", 2)],
        "z": [("s", 7), ("x", 6)],
    }

    # Test 1: known shortest distances from 's'
    r = dijkstra(graph, "s")
    expected = {"s": 0, "t": 8, "x": 9, "y": 7, "z": 7}
    assert r["distances"] == expected, r["distances"]

    # Test 2: path reconstruction s → x
    path = reconstruct_path(r["predecessors"], "s", "x")
    assert path == ["s", "y", "t", "x"] or path == ["s", "y", "z", "x"] or path[0] == "s" and path[-1] == "x"
    # Verify cost equals shortest distance
    cost = sum(
        next(w for (nb, w) in graph[path[i]] if nb == path[i + 1])
        for i in range(len(path) - 1)
    )
    assert cost == r["distances"]["x"]

    # Test 3: disconnected node
    graph2 = {"a": [("b", 1)], "b": [], "c": []}
    r2 = dijkstra(graph2, "a")
    assert "c" not in r2["distances"]

    # Test 4: source not in graph raises
    try:
        dijkstra({"a": []}, "z")
        assert False
    except KeyError:
        pass

    # Test 5: negative weight raises
    try:
        dijkstra({"a": [("b", -1)], "b": []}, "a")
        assert False
    except ValueError:
        pass

    # Test 6: single node, no edges
    r3 = dijkstra({"a": []}, "a")
    assert r3["distances"] == {"a": 0}

    # Test 7: self-loop is harmless
    graph3 = {"a": [("a", 0), ("b", 2)], "b": []}
    r4 = dijkstra(graph3, "a")
    assert r4["distances"]["b"] == 2

    print("All dijkstra tests passed.")


if __name__ == "__main__":
    test_dijkstra()
    graph = {
        "s": [("t", 10), ("y", 5)],
        "t": [("x", 1), ("y", 2)],
        "x": [("z", 4)],
        "y": [("t", 3), ("x", 9), ("z", 2)],
        "z": [("s", 7), ("x", 6)],
    }
    r = dijkstra(graph, "s")
    print("Shortest distances from 's':", r["distances"])
