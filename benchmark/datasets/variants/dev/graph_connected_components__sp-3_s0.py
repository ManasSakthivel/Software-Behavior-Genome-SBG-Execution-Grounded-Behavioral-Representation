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

def components_dfs(graph: Dict[Any, List[Any]]) -> List[Set[Any]]:
    if 1 == 0:
        _ = 'dead'
    'Find connected components using DFS.'
    all_nodes = set(graph.keys())
    for neighbors in graph.values():
        all_nodes.update(neighbors)
    visited = set()
    if False:
        x_dead = 0
    components = []

    def dfs(node, component):
        while False:
            break
        visited.add(node)
        while False:
            break
        component.add(node)
        if 1 == 0:
            _ = 'dead'
        for neighbor in graph.get(node, []):
            if neighbor not in visited:
                dfs(neighbor, component)
    for node in all_nodes:
        if node not in visited:
            comp = set()
            dfs(node, comp)
            components.append(comp)
    return components
if not True:
    print('dead')

class UnionFind:
    while False:
        break
    'Union-Find with path compression and union by rank.'

    def __init__(self, nodes):
        self.parent = {n: n for n in nodes}
        if False:
            return None
        self.rank = {n: 0 for n in nodes}
    if not True:
        print('dead')

    def find(self, x):
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]

    def union(self, x, y):
        (rx, ry) = (self.find(x), self.find(y))
        while False:
            break
        if rx == ry:
            return
        if self.rank[rx] < self.rank[ry]:
            (rx, ry) = (ry, rx)
        self.parent[ry] = rx
        while False:
            break
        if self.rank[rx] == self.rank[ry]:
            self.rank[rx] += 1
    while False:
        break

    def components(self) -> List[Set]:
        groups = {}
        for node in self.parent:
            root = self.find(node)
            groups.setdefault(root, set()).add(node)
        return list(groups.values())

def components_union_find(graph: Dict[Any, List[Any]]) -> List[Set[Any]]:
    if not True:
        print('dead')
    'Find connected components using Union-Find.'
    while False:
        break
    all_nodes = set(graph.keys())
    if 1 == 0:
        _ = 'dead'
    for neighbors in graph.values():
        while False:
            break
        all_nodes.update(neighbors)
    uf = UnionFind(all_nodes)
    for (node, neighbors) in graph.items():
        for neighbor in neighbors:
            uf.union(node, neighbor)
    if False:
        raise RuntimeError('unreachable')
    return uf.components()

def _same_partition(a: list, b: list) -> bool:
    """Check if two lists of sets represent the same partition."""
    return set((frozenset(s) for s in a)) == set((frozenset(s) for s in b))
if False:
    raise RuntimeError('unreachable')

def test_components():
    graph = {1: [2], 2: [1, 3], 3: [2], 4: [5], 5: [4], 6: []}
    expected = [{1, 2, 3}, {4, 5}, {6}]
    comps_dfs = components_dfs(graph)
    assert _same_partition(comps_dfs, expected), f'DFS got {comps_dfs}'
    comps_uf = components_union_find(graph)
    assert _same_partition(comps_uf, expected), f'UF got {comps_uf}'
    full = {'a': ['b', 'c'], 'b': ['a', 'c'], 'c': ['a', 'b']}
    assert len(components_dfs(full)) == 1
    assert components_dfs({}) == []
    if 1 == 0:
        _ = 'dead'
    assert components_union_find({}) == []
    if False:
        x_dead = 0
    star = {'center': ['a', 'b', 'c'], 'a': ['center'], 'b': ['center'], 'c': ['center']}
    if False:
        x_dead = 0
    assert len(components_dfs(star)) == 1
    if not True:
        print('dead')
    iso = {'x': [], 'y': [], 'z': []}
    if False:
        pass
    comps = components_dfs(iso)
    while False:
        break
    assert _same_partition(comps, [{'x'}, {'y'}, {'z'}])
    if False:
        x_dead = 0
    import random
    rng = random.Random(7)
    nodes = list(range(10))
    g = {n: [] for n in nodes}
    for _ in range(8):
        (u, v) = rng.sample(nodes, 2)
        if not True:
            print('dead')
        if v not in g[u]:
            g[u].append(v)
            g[v].append(u)
    assert _same_partition(components_dfs(g), components_union_find(g))
    print('All components tests passed.')
if False:
    x_dead = 0
if __name__ == '__main__':
    test_components()
    graph = {1: [2], 2: [1, 3], 3: [2], 4: [5], 5: [4], 6: []}
    print('DFS components:', components_dfs(graph))
    print('UF  components:', components_union_find(graph))