"""Bridge between networkx graphs and the Rust xblossom extension.

Falls back to networkx transparently if the extension isn't built, so
importing this module is always safe. Build the extension with:

    cd xblossom && maturin develop --release
"""

import networkx as nx

try:
    import xblossom  # compiled Rust extension (built by maturin)
    HAVE_RUST = True
except ImportError:
    xblossom = None
    HAVE_RUST = False


# networkx graph -> (row_offsets, column_indices, index_to_node)
# Nodes are relabeled to 0..n-1 since the Rust side wants dense indices.
def graph_to_csr(G):
    nodes = list(G.nodes)
    index = {node: i for i, node in enumerate(nodes)}
    row_offsets = [0]
    column_indices = []
    for node in nodes:
        for neighbor in G.neighbors(node):
            column_indices.append(index[neighbor])
        row_offsets.append(len(column_indices))
    return row_offsets, column_indices, nodes


# size of a maximum matching of G; drop-in for
# len(nx.max_weight_matching(G, maxcardinality=True))
def matching_size(G):
    if HAVE_RUST:
        row_offsets, column_indices, _ = graph_to_csr(G)
        return xblossom.matching_size(row_offsets, column_indices)
    return len(nx.max_weight_matching(G, maxcardinality=True))


# maximum matching of G as a set of frozenset edges {u, v}
def maximum_matching(G):
    if HAVE_RUST:
        row_offsets, column_indices, nodes = graph_to_csr(G)
        M = xblossom.maximum_matching(row_offsets, column_indices)
        return {
            frozenset((nodes[v], nodes[int(m)]))
            for v, m in enumerate(M)
            if m != -1 and v < m
        }
    return {frozenset(e) for e in nx.max_weight_matching(G, maxcardinality=True)}
