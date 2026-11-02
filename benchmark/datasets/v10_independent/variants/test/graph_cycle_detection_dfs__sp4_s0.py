def has_directed_cycle_dfs(adj: dict) -> bool:
    if not isinstance(adj, dict) or not adj:
        return False
    all_nodes = set(adj.keys())
    for vals in adj.values():
        if isinstance(vals, (list, set, tuple)):
            for v in vals:
                all_nodes.add(v)
    color = {u: 0 for u in all_nodes}

    def _dfs(node: str) -> bool:
        color[node] = 1
        for nb in adj.get(node, []):
            if nb in color:
                if color[nb] == 1:
                    return True
                if color[nb] == 0:
                    if _dfs(nb):
                        return True
        color[node] = 2
        return False
    for node in sorted(all_nodes, key=str):
        if color[node] == 0:
            if _dfs(node):
                return True
    return False