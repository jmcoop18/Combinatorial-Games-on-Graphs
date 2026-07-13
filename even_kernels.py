# old method, replaced by gf2_even_kernel.py
# *incomplete*

from graphs import (
    build_graph,
    prism_graph_nodes, prism_graph_adjacency_listing,
    tri_grid_graph_nodes, tri_grid_graph_adjacency_listing,
    path_graph_nodes, path_graph_adjacency_listing,
    cycle_graph_nodes, cycle_graph_adjacency_listing,
    wheel_graph_nodes, wheel_graph_adjacency_listing,
    complete_split_graph_nodes, complete_split_graph_adjacency_listing,
)

import networkx as nx
import matplotlib.pyplot as plt

from visualize import LAYOUTS as _LAYOUTS


def visualize_grid_kernel(G, S, notS, v=None, layout='grid'):
    pos = _LAYOUTS[layout](G)

    _, ax = plt.subplots()
    nx.draw_networkx_edges(G, pos, ax=ax)

    unvisited = sorted(n for n in G.nodes() if n not in S and n not in notS)

    # unvisited: light gray open circles
    nx.draw_networkx_nodes(G, pos, nodelist=unvisited, node_color='white',
                            edgecolors='lightgray', linewidths=1.5, ax=ax)
    # notS: open circles (white fill, black outline)
    nx.draw_networkx_nodes(G, pos, nodelist=sorted(notS), node_color='white',
                            edgecolors='black', linewidths=1.5, ax=ax)
    # S: solid filled circles
    nx.draw_networkx_nodes(G, pos, nodelist=sorted(S), node_color='black',
                            edgecolors='black', linewidths=1.5, ax=ax)

    if v is not None:
        nx.draw_networkx_nodes(G, pos, nodelist=[v], node_color='none',
                                edgecolors='red', linewidths=2.5, node_size=500, ax=ax)

    nx.draw_networkx_labels(G, pos, labels={n: n for n in unvisited + sorted(notS)},
                             font_size=8, font_color='black', ax=ax)
    nx.draw_networkx_labels(G, pos, labels={n: n for n in S},
                             font_size=8, font_color='white', ax=ax)

    ax.set_aspect('equal')
    ax.axis('off')
    plt.tight_layout()
    plt.show()


def find_even_kernel(G, v, S, notS, depth=0):

    neighbors = list(G.neighbors(v))
    notS.update([n for n in neighbors if n not in list(S | notS)])
    new_to_S = [] # records the vertices that are added to S for the next recursion

    for node in neighbors:
        adj = set(G.neighbors(node))
        kernel = sum(n in adj for n in S) # amount of adjacent vertices that are in S
        unmarked_vertices = sorted(adj - (S | notS))

        if kernel % 2 == 1 and len(unmarked_vertices) > 0:
            #if the ammount is odd, then add a vertex to S
            S.add(unmarked_vertices[0])
            new_to_S.append(unmarked_vertices[0])
            
            # once marked in S we can mark everything adjacent notS
            notS.update(list(G.neighbors(unmarked_vertices[0])))
            unmarked_vertices = unmarked_vertices[1:]

        # at this point we know that the vertex we are looking at is next to an even amout
        if len(unmarked_vertices) == 1:
            # if there is only 1 unmarked vertex then it can't be in S
            notS.add(unmarked_vertices[0])
            unmarked_vertices = unmarked_vertices[1:]

    # print("depth =",depth)
    # print("S =", S)
    # print("notS =", notS)
    # visualize_grid_kernel(G, S, notS, v)
    # print(new_to_S)

    [find_even_kernel(G, n, S, notS, depth+1) for n in new_to_S]


n = 3
G = build_graph(tri_grid_graph_nodes(n), tri_grid_graph_adjacency_listing(n))
layout = 'tri'
# G = build_graph(prism_graph_nodes(n), prism_graph_adjacency_listing(n))
# layout = 'prism'
v = (0,0)

# custom_nodes = [(0,0), (0,1), (0,2), (0,3), (0,4), (0,5),
#                 (1,0), (1,1), (1,2), (1,3), (1,4), (1,5),
#                 (2,0), (2,1), (2,2), (2,3), (2,4), (2,5),
#                 (3,0), (3,1), (3,2), (3,3), (3,4), (3,5),
#                 (4,0), (4,1), (4,2), (4,3), (4,4), (4,5)]
# custom_adjacency_listing = (
#     [((r, c), (r, c + 1)) for r in range(5) for c in range(5)] +
#     [((r, c), (r + 1, c)) for r in range(4) for c in range(6)]
# )
# G = build_graph(custom_nodes, custom_adjacency_listing)
# v = custom_nodes[0]

S = {v}
notS = set()

find_even_kernel(G, v, S, notS)
print("S =", S)
print("notS =", notS)

visualize_grid_kernel(G, S, notS, v, layout=layout)
