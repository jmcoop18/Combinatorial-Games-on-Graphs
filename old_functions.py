# ============================================================================
# A place to store old functions that I want documented but don't want to
# delete. These are earlier, slower nimber implementations kept for reference;
# the CLI uses the versions in nimber.py instead. Everything here still runs
# on its own, but is superseded.
# ============================================================================

import networkx as nx

from matching import AAC_winner
from nimber import mex


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
def memo_AAC_nimber(G, v, memo=None, msize=None):
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
        memo[key] = mex(memo_AAC_nimber(new_G, n, memo, msize) for n in G.neighbors(v))
    return memo[key]




# original MAC nimber calculator using brute-force and looking through the whole game tree
def recursive_MAC_nimber(G, v, seen=None):
    if seen is None:
        seen = set() # set of previously visited vertices
   
    if v in seen: 
        return 0
        
    neighbors = list(G.neighbors(v))
    
    if len(neighbors) == 0: 
        return 0

    new_seen = seen | {v}
    child_nimbers = []
    for n in neighbors:
        H = G.copy()
        H.remove_edge(v, n)
        child_nimbers.append(recursive_MAC_nimber(H, n, new_seen))
    return mex(child_nimbers)


# tried to implement memoization the way I did last time but it was slower
# the key is too expensive relative to the recursion it is replacing
def memo_MAC_nimber(G, v, seen=None, memo=None):
    if seen is None:
        seen = set() # set of previously visited vertices
        
    if memo is None:
        memo = {} # cache for previously calculated nimbers
    
    key = (frozenset(frozenset(e) for e in G.edges()), v, frozenset(seen))
    if key in memo:
        return memo[key]
        
    if v in seen: 
        memo[key] = 0
        return memo[key]
        
    neighbors = list(G.neighbors(v))
    
    if len(neighbors) == 0: 
        memo[key] = 0
        return memo[key]

    new_seen = seen | {v}
    child_nimbers = []
    for n in neighbors:
        H = G.copy()
        H.remove_edge(v, n)
        child_nimbers.append(memo_MAC_nimber(H, n, new_seen, memo))
    memo[key] = mex(child_nimbers)
    return memo[key]