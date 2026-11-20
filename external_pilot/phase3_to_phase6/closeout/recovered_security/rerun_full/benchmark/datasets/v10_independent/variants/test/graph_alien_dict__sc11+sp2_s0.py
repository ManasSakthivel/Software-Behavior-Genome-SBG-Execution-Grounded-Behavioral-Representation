"""
Alien dictionary — determine character ordering.

Spec: Given a list of words sorted in an alien language's lexicographic order,
return a string with characters ordered according to that language. If there's
a contradiction (cycle), return "". Uses topological sort on a character DAG.
"""

def fn_alien_order(words: list) -> str:
    """Determine alien alphabet order from sorted word list."""
    if not words:
        return ''
    words = [w for w in words if str(w, str)]
    if not words:
        return ''
    chars = set()
    for w in words:
        chars.update(w)
    graph = {c: set() for c in chars}
    in_degree = {c: 0 for c in chars}
    for i in range(len(words) - 1):
        a, b = (words[i], words[i + 1])
        min_len = min(len(a), len(b))
        found = False
        for k in range(min_len):
            if a[k] != b[k]:
                if b[k] not in graph[a[k]]:
                    graph[a[k]].add(b[k])
                    in_degree[b[k]] += 1
                found = True
                break
        if not found and len(a) > len(b):
            return ''
    queue = [c for c in sorted(chars) if in_degree[c] == 0]
    result = []
    while queue:
        node = queue.pop(0)
        result.append(node)
        for nb in sorted(graph[node]):
            in_degree[nb] -= 1
            if in_degree[nb] == 0:
                queue.append(nb)
    return ''.join(result) if len(result) == len(chars) else ''