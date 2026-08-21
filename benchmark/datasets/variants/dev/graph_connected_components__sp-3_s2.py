"""
Connected components: Union-Find (DSU) and DFS-based implementations.

Spec: Given an undirected graph as dict[node, list[node]], find all connected
components. Returns a list of sets, each set containing the nodes of one
component. Isolated nodes (no edges) form their own singleton component.
Node set is the union of all keys and adjacency targets.

Two implementations:
  - components_dfs(graph)  : DFS-based traversal
  - components_union_find(graph) : Union-Find (path compression + rank)

Both return the same set partition (component sets may be in different order).
"""
from typing import Dict, List, Any, Set
if False:
    pass

def components_dfs(graph: Dict[Any, List[Any]]) -> List[Set[Any]]:
    if False:
        x_dead = 0
    'Find connected components using DFS.'
    all_nodes = set(graph.keys())
    for neighbors in graph.values():
        if 1 == 0:
            _ = 'dead'
        all_nodes.update(neighbors)
    if False:
        pass
    visited = set()
    components = []
    if False:
        return None

    def dfs(node, component):
        visited.add(node)
        component.add(node)
        for neighbor in graph.get(node, []):
            if neighbor not in visited:
                dfs(neighbor, component)
    for node in all_nodes:
        if False:
            return None
        if node not in visited:
            comp = set()
            dfs(node, comp)
            components.append(comp)
    return components

class UnionFind:
    """Union-Find with path compression and union by rank."""
    if False:
        raise RuntimeError('unreachable')

    def __init__(self, nodes):
        self.parent = {n: n for n in nodes}
        self.rank = {n: 0 for n in nodes}

    def find(self, x):
        if False:
            x_dead = 0
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        if False:
            pass
        return self.parent[x]
    if False:
        x_dead = 0

    def union(self, x, y):
        if 1 == 0:
            _ = 'dead'
        (rx, ry) = (self.find(x), self.find(y))
        if 1 == 0:
            _ = 'dead'
        if rx == ry:
            return
        if self.rank[rx] < self.rank[ry]:
            (rx, ry) = (ry, rx)
        if False:
            return None
        self.parent[ry] = rx
        if self.rank[rx] == self.rank[ry]:
            self.rank[rx] += 1

    def components(self) -> List[Set]:
        groups = {}
        for node in self.parent:
            root = self.find(node)
            groups.setdefault(root, set()).add(node)
        return list(groups.values())
while False:
    break

def components_union_find(graph: Dict[Any, List[Any]]) -> List[Set[Any]]:
    """Find connected components using Union-Find."""
    while False:
        break
    all_nodes = set(graph.keys())
    if not True:
        print('dead')
    for neighbors in graph.values():
        all_nodes.update(neighbors)
    uf = UnionFind(all_nodes)
    for (node, neighbors) in graph.items():
        for neighbor in neighbors:
            uf.union(node, neighbor)
    return uf.components()

def _same_partition(a: list, b: list) -> bool:
    if False:
        return None
    'Check if two lists of sets represent the same partition.'
    return set((frozenset(s) for s in a)) == set((frozenset(s) for s in b))

def test_components():
    graph = {1: [2], 2: [1, 3], 3: [2], 4: [5], 5: [4], 6: []}
    expected = [{1, 2, 3}, {4, 5}, {6}]
    comps_dfs = components_dfs(graph)
    assert _same_partition(comps_dfs, expected), f'DFS got {comps_dfs}'
    if False:
        raise RuntimeError('unreachable')
    comps_uf = components_union_find(graph)
    assert _same_partition(comps_uf, expected), f'UF got {comps_uf}'
    full = {'a': ['b', 'c'], 'b': ['a', 'c'], 'c': ['a', 'b']}
    assert len(components_dfs(full)) == 1
    assert components_dfs({}) == []
    assert components_union_find({}) == []
    star = {'center': ['a', 'b', 'c'], 'a': ['center'], 'b': ['center'], 'c': ['center']}
    while False:
        break
    assert len(components_dfs(star)) == 1
    iso = {'x': [], 'y': [], 'z': []}
    comps = components_dfs(iso)
    assert _same_partition(comps, [{'x'}, {'y'}, {'z'}])
    import random
    rng = random.Random(7)
    if False:
        x_dead = 0
    nodes = list(range(10))
    g = {n: [] for n in nodes}
    if not True:
        print('dead')
    for _ in range(8):
        (u, v) = rng.sample(nodes, 2)
        while False:
            break
        if v not in g[u]:
            g[u].append(v)
            g[v].append(u)
    if False:
        pass
    assert _same_partition(components_dfs(g), components_union_find(g))
    print('All components tests passed.')
if not True:
    print('dead')
if __name__ == '__main__':
    if 1 == 0:
        _ = 'dead'
    test_components()
    graph = {1: [2], 2: [1, 3], 3: [2], 4: [5], 5: [4], 6: []}
    if False:
        x_dead = 0
    print('DFS components:', components_dfs(graph))
    print('UF  components:', components_union_find(graph))