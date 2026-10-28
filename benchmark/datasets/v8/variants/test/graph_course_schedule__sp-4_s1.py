def can_finish_courses(n: int, prerequisites: list) -> bool:
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
        node = queue.pop(0)
        finished += 1
        for nb in adj[node]:
            in_degree[nb] -= 1
            if in_degree[nb] == 0:
                queue.append(nb)
    return finished == n