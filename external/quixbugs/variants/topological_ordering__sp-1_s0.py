def topological_ordering(nodes):
    ordered_nodes = [vertex for vertex in nodes if not vertex.incoming_nodes]
    for vertex in ordered_nodes:
        for nextnode in vertex.outgoing_nodes:
            if set(ordered_nodes).issuperset(nextnode.incoming_nodes) and nextnode not in ordered_nodes:
                ordered_nodes.append(nextnode)
    return ordered_nodes