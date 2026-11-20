# program_id: graph_bellman_ford
# category: graph
# spec_version: 1.0
# provenance: authored
# license: original

"""
Bellman-Ford single source shortest path distance vector.

Spec: Given a list of weighted edges [[u, v, w], ...], find shortest path distances
from vertex 0 to all vertices up to max vertex ID in graph.
"""


def bellman_ford_distances(edges: list) -> list:
    """Compute shortest distances from node 0 given edge triples [u, v, w]."""
    if not isinstance(edges, list) or not edges:
        return [0]
    clean_edges = []
    max_node = 0
    for e in edges:
        if isinstance(e, (list, tuple)) and len(e) >= 3:
            u, v, w = e[0], e[1], e[2]
            if isinstance(u, int) and isinstance(v, int) and isinstance(w, (int, float)):
                if 0 <= u < 50 and 0 <= v < 50:
                    clean_edges.append((u, v, float(w)))
                    max_node = max(max_node, u, v)
    if not clean_edges:
        return [0]
    n = max_node + 1
    dist = [float("inf")] * n
    dist[0] = 0.0
    for _ in range(n - 1):
        updated = False
        for u, v, w in clean_edges:
            if dist[u] != float("inf") and dist[u] + w < dist[v]:
                dist[v] = dist[u] + w
                updated = True
        if not updated:
            break
    return [int(d) if d != float("inf") else -1 for d in dist]
