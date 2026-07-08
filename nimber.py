import networkx as nx

from matching import AAC_winner


# ============================================================================
# Functions to find Nimbers
# ============================================================================

# returns the mex (minimum excluded value) of the list input
# mex([0, 1, 3, 4]) -> returns 2
# mex([0, 1, 2, 3]) -> returns 4
def mex(values):
    values = set(values)
    m = 0
    while m in values:
        m += 1
    return m


# returns the nimber for AAC on a graph G from a starting vertex v
def find_nimber(G, v):
    M = nx.Graph()
    _, winner = AAC_winner(G, M, v)

    #if player 2 wins from this position, game nimber = 0
    if winner == 'P2':
        return 0

    # find and save all verticies connected to v
    new_vertices = list(G.neighbors(v))

    # make a copy of the game and remove v
    new_G = G.copy()
    new_G.remove_node(v)


    # recurse and save the nimbers for the layer below the node
    child_nimbers = [find_nimber(new_G, node) for node in new_vertices]
    return mex(child_nimbers)


# adds a star infront of number for *2, *3, ...
# returns * for n=1
# leaves 0 as is
def nimber_output(n):
    if n > 1:
        return f'*{n}'
    elif n == 1:
        return '*'
    elif n == 0:
        return 0
