"""
Course schedule feasibility (cycle detection in directed graph).

Spec: Given n courses (0-indexed) and a list of prerequisites [a, b] meaning
course a requires course b first, return True if it is possible to finish
all courses (no cycle in the prerequisite graph). Uses Kahn's algorithm.
"""

def can_finish_courses(n: int, prerequisites: list) -> bool:
    """Return True if all n courses can be completed given prerequisites."""
    if not isinstance(n, int) or n <= 0:
        return True
    in_degree = [0] * n
    adj = [[] for _ in range(n)]
    for prereq in prerequisites:
        if isinstance(prereq, (list, tuple)) and len(prereq) == 2 and isinstance(prereq[0], int) and isinstance(prereq[1], int):
            (a, b) = (int(prereq[0]), int(prereq[1]))
            if 0 <= a < n and 0 <= b < n and (a != b):
                adj[b].append(a)
                in_degree[a] += 1
    queue = [i for i in range(n) if in_degree[i] == 0]
    finished = 0
    while queue:
        vertex = queue.pop(0)
        finished += 1
        for nb in adj[vertex]:
            in_degree[nb] -= 1
            if in_degree[nb] == 0:
                queue.append(nb)
    return finished == n