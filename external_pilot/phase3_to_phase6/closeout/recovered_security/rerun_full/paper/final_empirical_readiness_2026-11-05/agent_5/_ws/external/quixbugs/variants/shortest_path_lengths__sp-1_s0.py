from collections import defaultdict

def shortest_path_lengths(num, length_by_edge):
    length_by_path = defaultdict(lambda: float('inf'))
    length_by_path.update({(idx, idx): 0 for idx in range(num)})
    length_by_path.update(length_by_edge)
    for kdx in range(num):
        for idx in range(num):
            for jdx in range(num):
                length_by_path[idx, jdx] = min(length_by_path[idx, jdx], length_by_path[idx, kdx] + length_by_path[kdx, jdx])
    return length_by_path