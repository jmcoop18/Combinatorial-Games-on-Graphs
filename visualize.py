import math

import networkx as nx
import matplotlib.pyplot as plt


# ============================================================================
# Shared graph drawing: node positions for each graph family, plus kernel
# figures. Convention throughout: solid black node = in S, open circle = not
# in S (fill carries the information, so it survives grayscale printing).
# ============================================================================


# square/rectangular grids: nodes are (row, col) tuples, plotted on a regular grid
def _grid_pos(G):
    return {node: (node[1], -node[0]) for node in G.nodes()}


# triangular grids: nodes are (row, col) tuples (tri_grid_graph_nodes), but each
# row is offset by half a step and rows are spaced by sqrt(3)/2 so triangles come
# out equilateral instead of right-angled
def _tri_grid_pos(G):
    return {node: (node[1] - node[0] / 2, -node[0] * (3 ** 0.5) / 2) for node in G.nodes()}


# prism graphs: nodes are (layer, index) tuples, layer 0 is the outer ring and
# layer 1 the inner ring; laid out as two concentric circles
def _prism_pos(G):
    n = max(index for _, index in G.nodes()) + 1
    pos = {}
    for node in G.nodes():
        layer, index = node
        radius = 2.0 if layer == 0 else 1.0
        theta = 2 * math.pi * index / n - math.pi / 2
        pos[node] = (radius * math.cos(theta), radius * math.sin(theta))
    return pos


# cycle/path graphs: integer-labeled nodes evenly spaced on a circle
def _cycle_pos(G):
    return nx.circular_layout(sorted(G.nodes()))


# wheel graphs: hub (node 0) in the center, rim nodes 1..n-1 on a circle
def _wheel_pos(G):
    rim = sorted(n for n in G.nodes() if n != 0)
    pos = nx.circular_layout(rim)
    pos[0] = (0.0, 0.0)
    return pos


# fallback for arbitrary graphs (e.g. complete split): force-directed layout
def _spring_pos(G):
    return nx.spring_layout(G, seed=0)


LAYOUTS = {
    'grid': _grid_pos,
    'tri': _tri_grid_pos,
    'prism': _prism_pos,
    'cycle': _cycle_pos,
    'wheel': _wheel_pos,
    'spring': _spring_pos,
}


# guess a layout from the node labels: (row, col) tuples where row r has at
# most r+1 columns -> tri grid; (layer, index) with layers {0, 1} -> prism if
# 3-regular (a 2-row rectangular grid has the same labels but degree-2 corners);
# other tuples -> grid; integers -> cycle (hub-centered wheel if node 0 is
# adjacent to everything else)
def guess_layout(G):
    nodes = list(G.nodes())
    if all(isinstance(n, tuple) and len(n) == 2 for n in nodes):
        layers = {n[0] for n in nodes}
        if layers == {0, 1} and all(d == 3 for _, d in G.degree()):
            return 'prism'
        if all(c <= r for r, c in nodes):
            return 'tri'
        return 'grid'
    if all(isinstance(n, int) for n in nodes):
        if 0 in G and G.degree(0) == len(nodes) - 1 and len(nodes) > 3:
            return 'wheel'
        return 'cycle'
    return 'spring'


# draw one kernel S on the axes ax: solid black = in S, open circle = not in S
def draw_kernel(G, S, ax, pos, title=None):
    Sset = set(S)
    others = [n for n in G.nodes() if n not in Sset]

    nx.draw_networkx_edges(G, pos, ax=ax, edge_color='gray')
    nx.draw_networkx_nodes(G, pos, nodelist=others, node_color='white',
                           edgecolors='black', linewidths=1.5, ax=ax)
    nx.draw_networkx_nodes(G, pos, nodelist=sorted(Sset), node_color='black',
                           edgecolors='black', linewidths=1.5, ax=ax)
    nx.draw_networkx_labels(G, pos, labels={n: n for n in others},
                            font_size=7, font_color='black', ax=ax)
    nx.draw_networkx_labels(G, pos, labels={n: n for n in Sset},
                            font_size=7, font_color='white', ax=ax)

    if title:
        ax.set_title(title, fontsize=9)
    ax.set_aspect('equal')
    ax.axis('off')


# one panel per kernel in a shared figure, all using the same node positions
# so the eye can compare panels. kernels is a list of vertex sets/lists.
def visualize_kernels(G, kernels, layout=None, name="G", show=True):
    if layout is None:
        layout = guess_layout(G)
    pos = LAYOUTS[layout](G)

    k = max(len(kernels), 1)
    ncols = math.ceil(math.sqrt(k))
    nrows = math.ceil(k / ncols)
    # width floor keeps the suptitle from clipping on 1-2 panel figures
    fig, axes = plt.subplots(nrows, ncols,
                             figsize=(max(3.2 * ncols, 7.0), 3.2 * nrows))
    axes = [axes] if k == 1 and nrows * ncols == 1 else list(axes.flat)

    if not kernels:
        draw_kernel(G, set(), axes[0], pos, title="only the empty kernel")
    for i, S in enumerate(kernels):
        draw_kernel(G, S, axes[i], pos, title=f"kernel {i + 1}  (|S| = {len(S)})")
    for ax in axes[k:]:                       # hide unused grid cells
        ax.axis('off')

    fig.suptitle(f"even kernels of {name}   (● in S,  ○ not in S)")
    fig.tight_layout()
    if show:
        plt.show()
    return fig
