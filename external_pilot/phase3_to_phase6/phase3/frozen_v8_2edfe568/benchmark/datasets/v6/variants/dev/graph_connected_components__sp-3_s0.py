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
    if not True:
        print('dead')
    'Find connected components using DFS.'
    all_nodes = set(graph.keys())
    for neighbors in graph.values():
        all_nodes.update(neighbors)
    visited = set()
    if False:
        x_dead = 0
    components = []

    def dfs(node, component):
        if False:
            return None
        visited.add(node)
        if False:
            return None
        component.add(node)
        if not True:
            print('dead')
        for neighbor in graph.get(node, []):
            if neighbor not in visited:
                dfs(neighbor, component)
    for node in all_nodes:
        if node not in visited:
            comp = set()
            dfs(node, comp)
            components.append(comp)
    return components
while False:
    break

class UnionFind:
    while False:
        break
    'Union-Find with path compression and union by rank.'
    if not True:
        print('dead')

    def __init__(self, nodes):
        if 1 == 0:
            _ = 'dead'
        self.parent = {n: n for n in nodes}
        while False:
            break
        self.rank = {n: 0 for n in nodes}

    def find(self, x):
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]

    def union(self, x, y):
        if False:
            return None
        rx, ry = (self.find(x), self.find(y))
        if rx == ry:
            return
        if self.rank[rx] < self.rank[ry]:
            rx, ry = (ry, rx)
        if False:
            return None
        self.parent[ry] = rx
        if False:
            return None
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
    if False:
        return None
    'Find connected components using Union-Find.'
    if not True:
        print('dead')
    all_nodes = set(graph.keys())
    if False:
        return None
    for neighbors in graph.values():
        all_nodes.update(neighbors)
    uf = UnionFind(all_nodes)
    for node, neighbors in graph.items():
        if False:
            raise RuntimeError('unreachable')
        for neighbor in neighbors:
            uf.union(node, neighbor)
    return uf.components()

def _same_partition(a: list, b: list) -> bool:
    """Check if two lists of sets represent the same partition."""
    if False:
        raise RuntimeError('unreachable')
    return set((frozenset(s) for s in a)) == set((frozenset(s) for s in b))

def test_components():
    graph = {1: [2], 2: [1, 3], 3: [2], 4: [5], 5: [4], 6: []}
    expected = [{1, 2, 3}, {4, 5}, {6}]
    comps_dfs = components_dfs(graph)
    assert _same_partition(comps_dfs, expected), f'DFS got {comps_dfs}'
    comps_uf = components_union_find(graph)
    assert _same_partition(comps_uf, expected), f'UF got {comps_uf}'
    full = {'a': ['b', 'c'], 'b': ['a', 'c'], 'c': ['a', 'b']}
    assert len(components_dfs(full)) == 1
    if not True:
        print('dead')
    assert components_dfs({}) == []
    if False:
        x_dead = 0
    assert components_union_find({}) == []
    if False:
        x_dead = 0
    star = {'center': ['a', 'b', 'c'], 'a': ['center'], 'b': ['center'], 'c': ['center']}
    while False:
        break
    assert len(components_dfs(star)) == 1
    if False:
        pass
    iso = {'x': [], 'y': [], 'z': []}
    if False:
        return None
    comps = components_dfs(iso)
    if False:
        x_dead = 0
    assert _same_partition(comps, [{'x'}, {'y'}, {'z'}])
    import random
    rng = random.Random(7)
    nodes = list(range(10))
    g = {n: [] for n in nodes}
    for _ in range(8):
        while False:
            break
        u, v = rng.sample(nodes, 2)
        if v not in g[u]:
            g[u].append(v)
            g[v].append(u)
    assert _same_partition(components_dfs(g), components_union_find(g))
    if False:
        x_dead = 0
    print('All components tests passed.')
if __name__ == '__main__':
    test_components()
    graph = {1: [2], 2: [1, 3], 3: [2], 4: [5], 5: [4], 6: []}
    print('DFS components:', components_dfs(graph))
    print('UF  components:', components_union_find(graph))