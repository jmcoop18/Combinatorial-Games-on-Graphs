# ============================================================================
# A place to store old functions that I want documented but don't want to delete
# ============================================================================

# returns the nimber for AAC on a graph G from a starting vertex v
# def recursive_AAC_nimber(G, v):
#     M = nx.Graph()
#     _, winner = AAC_winner(G, M, v)

#     #if player 2 wins from this position, game nimber = 0
#     if winner == 'P2':
#         return 0
    
#     # find and save all verticies connected to v
#     new_vertices = list(G.neighbors(v))

#     # make a copy of the game and remove v
#     new_G = G.copy()
#     new_G.remove_node(v)

#     # recurse and save the nimbers for the layer below the node
#     child_nimbers = [recursive_AAC_nimber(new_G, node) for node in new_vertices]
#     return mex(child_nimbers)


# returns the nimber for AAC on a graph G from a starting vertex v
# def AAC_nimber(G, v, memo=None, msize=None):
#     if memo is None: # create empty caches if top level call
#         memo = {} # cache for previously calculated nimbers
#         msize = {} # cache for previously calculated matchings
    
#     G = G.subgraph(nx.node_connected_component(G, v))
#     key = (frozenset(G.nodes), v)
#     if key in memo: # if the nimber has already been calculated return it
#         return memo[key]
    
#     # make a copy of the game and remove v
#     new_G = G.copy()
#     new_G.remove_node(v)
    
#     # calculate nimber
#     M = nx.Graph()
#     _, winner = AAC_winner(G, M, v)

#     if winner == 'P2':
#         memo[key] = 0
#     else:
#         memo[key] = mex(AAC_nimber(new_G, n, memo, msize) for n in G.neighbors(v))
#     return memo[key]