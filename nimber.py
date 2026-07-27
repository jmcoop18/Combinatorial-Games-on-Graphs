from functools import lru_cache

import networkx as nx

from rust_matching import matching_size as rust_matching_size


# ============================================================================
# Nimber Helper Functions
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

    
# ============================================================================
# Functions to find Nimbers For AAC
# ============================================================================

def nx_AAC_nimber(G, v, memo=None, msize=None):
    if memo is None: # create empty caches if top level call
        memo = {} # cache for previously calculated nimbers
        msize = {} # cache for previously calculated matchings

    G = G.subgraph(nx.node_connected_component(G, v))
    key = (frozenset(G.nodes), v)
    if key in memo: # if the nimber has already been calculated return it
        return memo[key]

    # returns the size of a maximum matching 
    def matching_size(H):
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



# same as nx_AAC_nimber but matchings are computed by the Rust blossom
# extension (xblossom); falls back to networkx if the extension isn't built
def blossomX_AAC_nimber(G, v, memo=None, msize=None):
    if memo is None: # create empty caches if top level call
        memo = {} # cache for previously calculated nimbers
        msize = {} # cache for previously calculated matchings

    G = G.subgraph(nx.node_connected_component(G, v))
    key = (frozenset(G.nodes), v)
    if key in memo: # if the nimber has already been calculated return it
        return memo[key]

    # returns the size of a maximum matching
    def matching_size(H):
        m = frozenset(H.nodes)
        if m not in msize: # add matching to the cache if it's a new calculation
            msize[m] = rust_matching_size(H)
        return msize[m]

    H = G.copy()
    H.remove_node(v)

    if matching_size(G) == matching_size(H):   # P2 wins -> nimber 0, prune subtree
        memo[key] = 0
    else:
        memo[key] = mex(blossomX_AAC_nimber(H, u, memo, msize) for u in G.neighbors(v))
    return memo[key]



# Closed-form solver for complete multipartite graphs K(sizes)
# max matching size of a complete multipartite graph with the given part counts
def multipartite_matching_size(counts):
    N = sum(counts)
    if N == 0:
        return 0
    return min(N // 2, N - max(counts))


# nimber of the position where the current vertex sits in a part with `own`
# vertices remaining (including itself); `others` = sorted sizes of other parts
@lru_cache(maxsize=None)
def _kpartite_AAC_nimber(others, own):
    counts = others + (own,)
    after = others + (own - 1,)
    if multipartite_matching_size(counts) == multipartite_matching_size(after):
        return 0  # P2 wins, prune subtree

    # next vertex must be in a different part
    rest = list(others)
    child_nimbers = []
    seen = set()
    for part, vertex in enumerate(rest):
        if vertex == 0:
            continue  # no vertex left in this part to move to
        new_others = tuple(sorted(rest[:part] + rest[part + 1:] + [own - 1]))
        key = (new_others, vertex)
        if key in seen:
            continue  # same position up to part relabeling
        seen.add(key)
        child_nimbers.append(_kpartite_AAC_nimber(new_others, vertex))
    return mex(child_nimbers)


# returns the nimber for AAC on K(sizes) starting from any vertex in part p
# e.g. multipartite_AAC_nimber([1, 2, 3, 4, 5, 6, 22], 6) -> start in the 22-part
def multipartite_AAC_nimber(sizes, p):
    others = tuple(sorted(list(sizes[:p]) + list(sizes[p + 1:])))
    return _kpartite_AAC_nimber(others, sizes[p])



# ============================================================================
# Functions to find Nimbers For MAC
# ============================================================================

     
# same as MAC_nimber, but the graph is packed into bitmasks 
# (adj[i] = bitmask of i's neighbors, 
# seen = bitmask of visited vertices) instead of copying a networkx Graph on every move;
# this makes the memo key (adj, v, seen_mask) cheap to build and hash, 
# so caching actually pays off
def bitmask_MAC_nimber(G, v):
    nodes = list(G.nodes)
    index = {u: i for i, u in enumerate(nodes)}
    adj = [0] * len(nodes)
    for a, b in G.edges():
        ia, ib = index[a], index[b]
        adj[ia] |= 1 << ib
        adj[ib] |= 1 << ia
    return _bitmask_MAC_nimber(tuple(adj), index[v], 0, {})


def _bitmask_MAC_nimber(adj, v, seen_mask, memo):
    bit = 1 << v
    if seen_mask & bit: return 0

    neighbors = adj[v]
    if neighbors == 0: return 0

    key = (adj, v, seen_mask)
    cached = memo.get(key)
    if cached is not None:
        return cached

    new_seen_mask = seen_mask | bit
    child_nimbers = []
    remaining = neighbors
    while remaining:
        low = remaining & -remaining      # isolate the lowest set bit
        n = low.bit_length() - 1          # bit position -> vertex index
        remaining ^= low                  # move on to the next neighbor

        new_adj = list(adj)
        new_adj[v] &= ~low
        new_adj[n] &= ~bit
        child_nimbers.append(_bitmask_MAC_nimber(tuple(new_adj), n, new_seen_mask, memo))

    result = mex(child_nimbers)
    memo[key] = result
    return result



if __name__ == "__main__":
    pass