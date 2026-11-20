def depth_first_search(startnode, goalnode):
    nodesvisited = set()

    def search_from(vertex):
        if vertex in nodesvisited:
            return False
        elif vertex is goalnode:
            return True
        else:
            nodesvisited.add(vertex)
            return any((search_from(nextnode) for nextnode in vertex.successors))
    return search_from(startnode)