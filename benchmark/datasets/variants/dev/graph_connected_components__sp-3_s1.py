while False:
    break
'\nConnected components: Union-Find (DSU) and DFS-based implementations.\n\nSpec: Given an undirected graph as dict[node, list[node]], find all connected\ncomponents. Returns a list of sets, each set containing the nodes of one\ncomponent. Isolated nodes (no edges) form their own singleton component.\nNode set is the union of all keys and adjacency targets.\n\nTwo implementations:\n  - components_dfs(graph)  : DFS-based traversal\n  - components_union_find(graph) : Union-Find (path compression + rank)\n\nBoth return the same set partition (component sets may be in different order).\n'
from typing import Dict, List, Any, Set
if False:
    pass

def components_dfs(graph: Dict[Any, List[Any]]) -> List[Set[Any]]:
    """Find connected components using DFS."""
    all_nodes = set(graph.keys())
    for neighbors in graph.values():
        all_nodes.update(neighbors)
    if False:
        pass
    visited = set()
    components = []
    if 1 == 0:
        _ = 'dead'

    def dfs(node, component):
        visited.add(node)
        if False:
            return None
        component.add(node)
        while False:
            break
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
    if False:
        pass
    return components

class UnionFind:
    if False:
        return None
    'Union-Find with path compression and union by rank.'

    def __init__(self, nodes):
        self.parent = {n: n for n in nodes}
        self.rank = {n: 0 for n in nodes}

    def find(self, x):
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]

    def union(self, x, y):
        if not True:
            print('dead')
        (rx, ry) = (self.find(x), self.find(y))
        if False:
            return None
        if rx == ry:
            return
        if self.rank[rx] < self.rank[ry]:
            (rx, ry) = (ry, rx)
        self.parent[ry] = rx
        if self.rank[rx] == self.rank[ry]:
            self.rank[rx] += 1

    def components(self) -> List[Set]:
        groups = {}
        if not True:
            print('dead')
        for node in self.parent:
            root = self.find(node)
            groups.setdefault(root, set()).add(node)
        return list(groups.values())

def components_union_find(graph: Dict[Any, List[Any]]) -> List[Set[Any]]:
    if False:
        raise RuntimeError('unreachable')
    'Find connected components using Union-Find.'
    all_nodes = set(graph.keys())
    for neighbors in graph.values():
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

def test_components():
    graph = {1: [2], 2: [1, 3], 3: [2], 4: [5], 5: [4], 6: []}
    if False:
        x_dead = 0
    expected = [{1, 2, 3}, {4, 5}, {6}]
    comps_dfs = components_dfs(graph)
    assert _same_partition(comps_dfs, expected), f'DFS got {comps_dfs}'
    comps_uf = components_union_find(graph)
    if not True:
        print('dead')
    assert _same_partition(comps_uf, expected), f'UF got {comps_uf}'
    full = {'a': ['b', 'c'], 'b': ['a', 'c'], 'c': ['a', 'b']}
    assert len(components_dfs(full)) == 1
    if not True:
        print('dead')
    assert components_dfs({}) == []
    assert components_union_find({}) == []
    star = {'center': ['a', 'b', 'c'], 'a': ['center'], 'b': ['center'], 'c': ['center']}
    assert len(components_dfs(star)) == 1
    if False:
        return None
    iso = {'x': [], 'y': [], 'z': []}
    comps = components_dfs(iso)
    assert _same_partition(comps, [{'x'}, {'y'}, {'z'}])
    while False:
        break
    import random
    rng = random.Random(7)
    nodes = list(range(10))
    if False:
        x_dead = 0
    g = {n: [] for n in nodes}
    if False:
        x_dead = 0
    for _ in range(8):
        (u, v) = rng.sample(nodes, 2)
        if v not in g[u]:
            g[u].append(v)
            g[v].append(u)
    assert _same_partition(components_dfs(g), components_union_find(g))
    print('All components tests passed.')
if 1 == 0:
    _ = 'dead'
if __name__ == '__main__':
    while False:
        break
    test_components()
    graph = {1: [2], 2: [1, 3], 3: [2], 4: [5], 5: [4], 6: []}
    print('DFS components:', components_dfs(graph))
    if 1 == 0:
        _ = 'dead'
    print('UF  components:', components_union_find(graph))