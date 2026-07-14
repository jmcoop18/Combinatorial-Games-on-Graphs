import networkx as nx


# ============================================================================
# Graph construction: prism, triangular grid, path, cycle, wheel, and complete
# split graphs, plus arbitrary adjacency listings, all funnel through build_graph()
# ============================================================================

# returns list of (layer, index) vertex labels for a prism graph with n sides:
# layer 0 is the outer ring, layer 1 is the inner ring, each indexed 0..n-1
def prism_graph_nodes(n):
    return [(0, i) for i in range(n)] + [(1, i) for i in range(n)]


# returns adjacency listing for prism graph with n sides
# vertices are labeled (layer, index): (0, i) is on the outer ring, (1, i) on the inner ring
def prism_graph_adjacency_listing(n):
    L = []
    # outer edges
    for i in range(n):
        L.append(((0, i), (0, (i + 1) % n)))

    # spokes
    for i in range(n):
        L.append(((0, i), (1, i)))

    # inner edges
    for i in range(n):
        L.append(((1, i), (1, (i + 1) % n)))

    return L


# returns list of (layer, index) vertex labels for a triangular grid graph with n rows of triangles
def tri_grid_graph_nodes(n):
    return [(r, c) for r in range(n + 1) for c in range(r + 1)]


# returns adjacent listing for triangular grid graph with n sides
# vertices are labeled (layer, index): the top vertex is (0,0), the row
# below it is (1,0) and (1,1), the next row is (2,0), (2,1), (2,2), etc.
def tri_grid_graph_adjacency_listing(n):
    L = []
    for r in range(n):
        # connect each vertex in row r down to the 2 vertices below it in row r+1
        for c in range(r + 1):
            L.append(((r, c), (r + 1, c)))
            L.append(((r, c), (r + 1, c + 1)))

        # connect vertices horizontally along row r+1
        for c in range(r + 1):
            L.append(((r + 1, c), (r + 1, c + 1)))
    return L


# returns list of vertex labels 0..n-1 for a path graph with n vertices
def path_graph_nodes(n):
    return list(range(n))


# returns adjacency listing for a path graph with n vertices: 0-1-2-...-(n-1)
def path_graph_adjacency_listing(n):
    return [(i, i + 1) for i in range(n - 1)]


# returns list of vertex labels 0..n-1 for a cycle graph with n vertices
def cycle_graph_nodes(n):
    return list(range(n))


# returns adjacency listing for a cycle graph with n vertices: 0-1-...-(n-1)-0
def cycle_graph_adjacency_listing(n):
    return [(i, (i + 1) % n) for i in range(n)]


# returns list of vertex labels for a wheel graph with n vertices total:
# vertex 0 is the hub, vertices 1..n-1 form the outer cycle
def wheel_graph_nodes(n):
    return list(range(n))


# returns adjacency listing for a wheel graph with n vertices total
def wheel_graph_adjacency_listing(n):
    L = []
    # rim edges
    for i in range(1, n):
        L.append((i, i % (n - 1) + 1))

    # spokes
    for i in range(1, n):
        L.append((0, i))

    return L


# returns list of vertex labels for a wheel graph with n vertices total:
# vertices 0... m-1 are the complete graph, is the hub
# vertices m... n-1 are the independent nodes
def complete_split_graph_nodes(m, n):
    return list(range(m + n))


# returns adjacency listing for complete split graph Km + Kn
def complete_split_graph_adjacency_listing(m, n):
    L = []

    # inner edges
    for i in range(m):
        for j in range(i + 1, m):
            L.append((i, j))

    # outer edges
    for i in range(m):
        for j in range(m, m + n):
            L.append((i, j))

    return L


# returns list of vertex labels 0..n-1 for the complete graph Kn
def complete_graph_nodes(n):
    return list(range(n))


# returns adjacency listing for the complete graph Kn: every pair of vertices
def complete_graph_adjacency_listing(n):
    return [(i, j) for i in range(n) for j in range(i + 1, n)]


# returns list of (part, index) vertex labels for the complete multipartite
# graph K(sizes[0], ..., sizes[-1]) where part p has sizes[p] vertices
def complete_multipartite_graph_nodes(sizes):
    return [(p, i) for p, size in enumerate(sizes) for i in range(size)]


# returns adjacency listing for K(sizes...): every pair of vertices in
# different parts is joined, no edges within a part
def complete_multipartite_graph_adjacency_listing(sizes):
    nodes = complete_multipartite_graph_nodes(sizes)
    return [(u, w) for a, u in enumerate(nodes) for w in nodes[a + 1:]
            if u[0] != w[0]]


# returns list of (row, col) vertex labels for a rectangular grid graph
# with m rows and n columns
def rect_grid_graph_nodes(m, n):
    return [(r, c) for r in range(m) for c in range(n)]


# returns adjacency listing for the m-row by n-column rectangular grid:
# each vertex connects to its right and downward neighbors
def rect_grid_graph_adjacency_listing(m, n):
    L = []
    for r in range(m):
        for c in range(n):
            if c + 1 < n:
                L.append(((r, c), (r, c + 1)))
            if r + 1 < m:
                L.append(((r, c), (r + 1, c)))
    return L


# build graph from adj listing
# nodes can be an int (creates nodes 0..nodes-1) or an explicit iterable of node labels
def build_graph(nodes, listing):
    graph = nx.Graph()
    if isinstance(nodes, int):
        graph.add_nodes_from(range(nodes))
    else:
        graph.add_nodes_from(nodes)
    graph.add_edges_from(listing)

    return graph
