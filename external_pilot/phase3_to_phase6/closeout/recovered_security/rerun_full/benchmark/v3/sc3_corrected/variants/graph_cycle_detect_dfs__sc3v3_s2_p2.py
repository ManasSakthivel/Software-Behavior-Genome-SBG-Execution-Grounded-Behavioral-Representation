# program_id: graph_cycle_detect_dfs
# category: graph_algorithms
# spec_version: 1.0

"""
Cycle detection in directed and undirected graphs using DFS coloring.

Spec: Provides two functions:
  - has_cycle_directed(graph)   : detect cycles in a directed graph using
    3-color DFS (WHITE=unvisited, GRAY=in-stack, BLACK=done). Returns
    (bool, list_of_cycle_nodes_or_None).
  - has_cycle_undirected(graph) : detect cycles in an undirected graph by
    tracking the parent node during DFS. Returns bool.

Graph is dict[node, list[node]]. Node set inferred from keys + adjacency.
Neither function raises on empty input (returns False/None).
"""
from typing import Dict, List, Any, Optional, Tuple


def has_cycle_directed(graph: Dict[Any, List[Any]]) -> Tuple[bool, Optional[List]]:
    """
    Detect cycle in a directed graph. Returns (True, cycle_nodes) or (False, None).
    cycle_nodes is a list forming the cycle (approximate; first back-edge found).
    """
    all_nodes = set(graph.keys())
    for nbrs in graph.values():
        all_nodes.update(nbrs)

    WHITE, GRAY, BLACK = 0, 1, 2
    color = {n: WHITE for n in all_nodes}
    stack = []

    def dfs(u) -> bool:
        color[u] = GRAY
        stack.append(u)
        for v in graph.get(u, []):
            if color[v] == GRAY:
                # Found back-edge u→v; extract cycle from stack
                idx = stack.index(v)
                return True, stack[idx:]
            if color[v] == WHITE:
                result = dfs(v)
                if result is not True and result[0]:
                    return result
        stack.pop()
        color[u] = BLACK
        return False, None

    for node in all_nodes:
        if color[node] == WHITE:
            found, cycle = dfs(node)
            if found:
                return True, cycle

    return False, None


def has_cycle_undirected(graph: Dict[Any, List[Any]]) -> bool:
    """Detect cycle in an undirected graph using DFS + parent tracking."""
    all_nodes = set(graph.keys())
    for nbrs in graph.values():
        all_nodes.update(nbrs)

    visited = set()

    def dfs(u, parent) -> bool:
        visited.add(u)
        for v in graph.get(u, []):
            if v not in visited:
                if dfs(v, u):
                    return True
            elif v != parent:
                return True  # back edge that isn't the tree edge we came from
        return False

    for node in all_nodes:
        if node not in visited:
            if dfs(node, None):
                return True
    return False


# ---------- tests ----------

def test_cycle_detection():
    # Test 1: DAG — no cycle
    dag = {1: [2, 3], 2: [4], 5: [4], 4: []}
    found, cycle = has_cycle_directed(dag)
    assert not found

    # Test 2: directed cycle 1→2→3→1
    cyclic = {1: [2], 2: [3], 3: [1]}
    found, cycle = has_cycle_directed(cyclic)
    assert found
    assert cycle is not None and len(cycle) >= 2

    # Test 3: self-loop
    self_loop = {1: [1], 2: []}
    found, _ = has_cycle_directed(self_loop)
    assert found

    # Test 4: undirected — no cycle (tree)
    tree = {"a": ["b", "c"], "b": ["a"], "c": ["a"]}
    assert not has_cycle_undirected(tree)

    # Test 5: undirected — cycle (triangle)
    triangle = {"a": ["b", "c"], "b": ["a", "c"], "c": ["a", "b"]}
    assert has_cycle_undirected(triangle)

    # Test 6: empty graphs
    found_e, _ = has_cycle_directed({})
    assert not found_e
    assert not has_cycle_undirected({})

    # Test 7: disconnected directed graph with cycle in one component
    mixed = {1: [2], 2: [3], 3: [2], 4: [5], 5: []}
    found_m, _ = has_cycle_directed(mixed)
    assert found_m

    # Test 8: long directed chain — no cycle
    chain = {i: [i + 1] for i in range(20)}
    chain[20] = []
    found_c, _ = has_cycle_directed(chain)
    assert not found_c

    print("All cycle detection tests passed.")


if __name__ == "__main__":
    test_cycle_detection()
    print("Directed cycle in {1→2→3→1}:", has_cycle_directed({1: [2], 2: [3], 3: [1]}))
    print("Undirected cycle in triangle:", has_cycle_undirected({"a": ["b","c"],"b": ["a","c"],"c": ["a","b"]}))
