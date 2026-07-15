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

# returns the nimber for AAC on a graph G from a starting vertex v
def recursive_AAC_nimber(G, v):
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
    child_nimbers = [recursive_AAC_nimber(new_G, node) for node in new_vertices]
    return mex(child_nimbers)


# returns the nimber for AAC on a graph G from a starting vertex v
def AAC_nimber(G, v, memo=None, msize=None):
    if memo is None: # create empty caches if top level call
        memo = {} # cache for previously calculated nimbers
        msize = {} # cache for previously calculated matchings
    
    G = G.subgraph(nx.node_connected_component(G, v))
    key = (frozenset(G.nodes), v)
    if key in memo: # if the nimber has already been calculated return it
        return memo[key]
    
    # make a copy of the game and remove v
    new_G = G.copy()
    new_G.remove_node(v)
    
    # calculate nimber
    M = nx.Graph()
    _, winner = AAC_winner(G, M, v)

    if winner == 'P2':
        memo[key] = 0
    else:
        memo[key] = mex(AAC_nimber(new_G, n, memo, msize) for n in G.neighbors(v))
    return memo[key]




def nx_AAC_nimber(G, v, memo=None, msize=None):
    if memo is None: # create empty caches if top level call
        memo = {} # cache for previously calculated nimbers
        msize = {} # cache for previously calculated matchings

    G = G.subgraph(nx.node_connected_component(G, v))   # 3
    key = (frozenset(G.nodes), v)
    if key in memo: # if the nimber has already been calculated return it
        return memo[key]

    # returns the size of a maximum matching 
    def matching_size(H):                                # 2 + 4
        m = frozenset(H.nodes)
        if m not in msize: # add matching to the cache if it's a new calculation
            msize[m] = len(nx.max_weight_matching(H, maxcardinality=True))
        return msize[m]
    
    H = G.copy()
    H.remove_node(v)

    if matching_size(G) == matching_size(H):   # P2 wins -> nimber 0, prune subtree
        memo[key] = 0
    else:
        memo[key] = mex(nx_AAC_nimber(H, u, memo, msize) for u in G.neighbors(v))
    return memo[key]


def MAC_nimber(G,v):
    # if one node left, then p2 win and nimber = 0
    if len(G) == 1:
        return 0
    
    neighbors = list(G.neighbors(v))
    
    child_nimbers = [MAC_nimber(G.remove_edge(v, n), n) for n in neighbors]
    return mex(child_nimbers)



if __name__ == "__main__":
    from graphs import prism_graph_adjacency_listing, prism_graph_nodes, build_graph
    
    n = 3
    G = build_graph(prism_graph_nodes(n), prism_graph_adjacency_listing(n))
    v= (0,0)
    print(MAC_nimber(G, v))