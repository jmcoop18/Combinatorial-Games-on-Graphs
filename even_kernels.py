# Earlier, incomplete even-kernel approach, superseded by gf2_even_kernel.py.
# Kept as a baseline/reference; not used by the CLI. find_even_kernel greedily
# walks outward from a vertex trying to build an even kernel, but doesn't
# explore every branch, so it can miss kernels the GF(2) solver finds.

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

    [find_even_kernel(G, n, S, notS, depth+1) for n in new_to_S]


