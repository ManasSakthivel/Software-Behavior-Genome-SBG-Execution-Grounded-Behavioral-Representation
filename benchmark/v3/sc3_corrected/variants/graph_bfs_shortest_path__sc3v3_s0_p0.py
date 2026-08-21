# program_id: graph_bfs_shortest_path
# category: graph_algorithms
# spec_version: 1.0

"""
Breadth-First Search: shortest path (hop count) and level-order traversal.

Spec: Given an unweighted directed or undirected graph represented as an
adjacency list (dict[node, list[node]]), and a source node, compute:
  - The shortest path (fewest edges) from source to every reachable node.
  - The predecessor map for path reconstruction.
  - The BFS level (distance) for each reachable node.

bfs(graph, source) → dict with keys 'distances', 'predecessors', 'order'
reconstruct_path(predecessors, source, target) → list of nodes or None if unreachable.
Raises KeyError if source is not in graph.
"""
from collections import deque
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
        raise KeyError(f"Source node {source!r} not in graph")

    distances = {source: 0}
    predecessors = {source: None}
    order = []
    queue = deque([source])

    while queue:
        node = queue.popleft()
        order.append(node)
        for neighbor in graph.get(node, []):
            if neighbor not in distances:
                distances[neighbor] = distances[node] + 1
                predecessors[neighbor] = node
                queue.append(neighbor)

    return {"distances": distances, "predecessors": predecessors, "order": order}


def reconstruct_path(predecessors: dict, source: Any, target: Any) -> Optional[List]:
    """Reconstruct the shortest path from source to target using predecessor map."""
    if target not in predecessors:
        return None  # unreachable

    path = []
    current = target
    while current is not None:
        path.append(current)
        current = predecessors[current]
    path.reverse()

    if path[0] != source:
        return None  # disconnected
    return path


# ---------- tests ----------

def test_bfs():
    # Graph: 0→1, 0→2, 1→3, 2→3, 3→4
    graph = {
        0: [1, 2],
        1: [3],
        3: [3],
        3: [4],
        4: [],
    }

    # Test 1: distances from 0
    result = bfs(graph, 0)
    assert result["distances"] == {0: 0, 1: 1, 2: 1, 3: 2, 4: 3}, result["distances"]

    # Test 2: order visits nodes level by level
    assert result["order"][0] == 0
    assert set(result["order"][1:3]) == {1, 2}

    # Test 3: path reconstruction
    path = reconstruct_path(result["predecessors"], 0, 4)
    assert path[0] == 0 and path[-1] == 4
    assert len(path) == 4  # 0→?→3→4

    # Test 4: source unreachable from itself (trivial)
    path_self = reconstruct_path(result["predecessors"], 0, 0)
    assert path_self == [0]

    # Test 5: disconnected node is unreachable
    graph2 = {0: [1], 1: [], 2: [3], 3: []}
    result2 = bfs(graph2, 0)
    assert 2 not in result2["distances"]
    assert reconstruct_path(result2["predecessors"], 0, 3) is None

    # Test 6: undirected-style graph (symmetric adjacency)
    ug = {
        "A": ["B", "C"],
        "B": ["A", "D"],
        "C": ["A"],
        "D": ["B"],
    }
    r = bfs(ug, "A")
    assert r["distances"]["D"] == 2

    # Test 7: source not in graph raises KeyError
    try:
        bfs({0: []}, 99)
        assert False
    except KeyError:
        pass

    print("All bfs tests passed.")


if __name__ == "__main__":
    test_bfs()
    graph = {0: [1, 2], 1: [3], 2: [3], 3: [4], 4: []}
    result = bfs(graph, 0)
    print(f"Distances from 0: {result['distances']}")
    print(f"Path 0→4: {reconstruct_path(result['predecessors'], 0, 4)}")
