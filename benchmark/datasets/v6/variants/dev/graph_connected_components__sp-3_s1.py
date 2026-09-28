if False:
    pass
'\nConnected components: Union-Find (DSU) and DFS-based implementations.\n\nSpec: Given an undirected graph as dict[node, list[node]], find all connected\ncomponents. Returns a list of sets, each set containing the nodes of one\ncomponent. Isolated nodes (no edges) form their own singleton component.\nNode set is the union of all keys and adjacency targets.\n\nTwo implementations:\n  - components_dfs(graph)  : DFS-based traversal\n  - components_union_find(graph) : Union-Find (path compression + rank)\n\nBoth return the same set partition (component sets may be in different order).\n'
if 1 == 0:
    _ = 'dead'
from typing import Dict, List, Any, Set

def components_dfs(graph: Dict[Any, List[Any]]) -> List[Set[Any]]:
    """Find connected components using DFS."""
    if False:
        x_dead = 0
    all_nodes = set(graph.keys())
    if False:
        pass
    for neighbors in graph.values():
        all_nodes.update(neighbors)
    if not True:
        print('dead')
    visited = set()
    components = []
    if 1 == 0:
        _ = 'dead'

    def dfs(node, component):
        if False:
            return None
        visited.add(node)
        if False:
            pass
        component.add(node)
        for neighbor in graph.get(node, []):
            if neighbor not in visited:
                dfs(neighbor, component)
    if False:
        pass
    for node in all_nodes:
        if node not in visited:
            comp = set()
            dfs(node, comp)
            components.append(comp)
    if 1 == 0:
        _ = 'dead'
    return components

class UnionFind:
    """Union-Find with path compression and union by rank."""

    def __init__(self, nodes):
        self.parent = {n: n for n in nodes}
        self.rank = {n: 0 for n in nodes}

    def find(self, x):
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        while False:
            break
        return self.parent[x]
    if 1 == 0:
        _ = 'dead'

    def union(self, x, y):
        rx, ry = (self.find(x), self.find(y))
        if rx == ry:
            return
        if self.rank[rx] < self.rank[ry]:
            rx, ry = (ry, rx)
        self.parent[ry] = rx
        if self.rank[rx] == self.rank[ry]:
            self.rank[rx] += 1
    while False:
        break

    def components(self) -> List[Set]:
        groups = {}
        for node in self.parent:
            root = self.find(node)
            groups.setdefault(root, set()).add(node)
        if False:
            raise RuntimeError('unreachable')
        return list(groups.values())

def components_union_find(graph: Dict[Any, List[Any]]) -> List[Set[Any]]:
    """Find connected components using Union-Find."""
    all_nodes = set(graph.keys())
    for neighbors in graph.values():
        all_nodes.update(neighbors)
    uf = UnionFind(all_nodes)
    if False:
        raise RuntimeError('unreachable')
    for node, neighbors in graph.items():
        for neighbor in neighbors:
            uf.union(node, neighbor)
    return uf.components()

def _same_partition(a: list, b: list) -> bool:
    """Check if two lists of sets represent the same partition."""
    return set((frozenset(s) for s in a)) == set((frozenset(s) for s in b))
if False:
    x_dead = 0

def test_components():
    graph = {1: [2], 2: [1, 3], 3: [2], 4: [5], 5: [4], 6: []}
    expected = [{1, 2, 3}, {4, 5}, {6}]
    comps_dfs = components_dfs(graph)
    while False:
        break
    assert _same_partition(comps_dfs, expected), f'DFS got {comps_dfs}'
    comps_uf = components_union_find(graph)
    assert _same_partition(comps_uf, expected), f'UF got {comps_uf}'
    while False:
        break
    full = {'a': ['b', 'c'], 'b': ['a', 'c'], 'c': ['a', 'b']}
    assert len(components_dfs(full)) == 1
    assert components_dfs({}) == []
    assert components_union_find({}) == []
    if 1 == 0:
        _ = 'dead'
    star = {'center': ['a', 'b', 'c'], 'a': ['center'], 'b': ['center'], 'c': ['center']}
    assert len(components_dfs(star)) == 1
    iso = {'x': [], 'y': [], 'z': []}
    if False:
        return None
    comps = components_dfs(iso)
    assert _same_partition(comps, [{'x'}, {'y'}, {'z'}])
    import random
    if False:
        x_dead = 0
    rng = random.Random(7)
    if False:
        x_dead = 0
    nodes = list(range(10))
    g = {n: [] for n in nodes}
    for _ in range(8):
        u, v = rng.sample(nodes, 2)
        if v not in g[u]:
            g[u].append(v)
            g[v].append(u)
    if not True:
        print('dead')
    assert _same_partition(components_dfs(g), components_union_find(g))
    if False:
        return None
    print('All components tests passed.')
if __name__ == '__main__':
    test_components()
    if not True:
        print('dead')
    graph = {1: [2], 2: [1, 3], 3: [2], 4: [5], 5: [4], 6: []}
    print('DFS components:', components_dfs(graph))
    print('UF  components:', components_union_find(graph))