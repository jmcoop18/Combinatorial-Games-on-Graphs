import copy

import networkx as nx


# ============================================================================
# Edmonds' blossom algorithm: augmenting-path search with blossom
# contraction/lifting, driven to a maximum matching by find_maximum_matching
# ============================================================================

# INPUT:  Graph G, initial matching M on G
# OUTPUT: maximum matching M* on G
def find_maximum_matching(G, M):
    P = find_augmenting_path(G, M) # my algorithm
    # P = find_augmenting_path_max_matching(G, M) # networkx version
    # P = find_augmenting_path_micali_vazirani(G, M) # vazirani version 

    if P == []:  # Base case
        return M
    else:  # Update matching based on P
        for i in range(len(P) - 1):
            if i % 2 == 0:  # unmatched edge
                M.add_edge(P[i], P[i + 1])
            else:  # matched edge
                M.remove_edge(P[i], P[i + 1])
        return find_maximum_matching(G, M)


# returns the len of the path from a point to its root
def dist_to_root(point, root, Graph):
    path = nx.shortest_path(Graph, source=point, target=root)
    return len(path) - 1


# 
def find_augmenting_path(G, M, Blossom_stack=None):
    if Blossom_stack is None:
        Blossom_stack = []
    F = []  # forest
    P = []  # final path

    unmarked_edges = list(set(G.edges()) - set(M.edges()))
    F_vertices = []
    tree_to_root = {}  # key=idx of tree in forest, val=root

    # List of exposed vertices - ROOTS OF TREES
    exp_vertices = list(set(G.nodes()) - set(M.nodes()))

    counter = 0
    # List of trees with the exposed vertices as the roots
    for v in exp_vertices:
        temp = nx.Graph()
        temp.add_node(v)
        F.append(temp)
        F_vertices.append(v)

        # link each root to its tree
        tree_to_root[counter] = v
        counter += 1

    for v in F_vertices:
        root_of_v = None
        tree_num_of_v = None
        for tree_num in range(len(F)):
            tree_in = F[tree_num]
            if tree_in.has_node(v):
                root_of_v = tree_to_root[tree_num]
                tree_num_of_v = tree_num
                break  # Break out of the for loop

        edges_v = list(G.edges(v))
        for edge_num in range(len(edges_v)):
            e = edges_v[edge_num]
            e2 = (e[1], e[0])  # the edge in the other order
            if (e in unmarked_edges or e2 in unmarked_edges) and e != []:
                w = e[1]  # the other vertex of the unmarked edge
                w_in_Forest = False  # Indicator for w in F or not

                # Go through all the trees in the forest to check if w in F
                tree_of_w = None
                tree_num_of_w = None
                for tree_number in range(len(F)):
                    tree = F[tree_number]
                    if tree.has_node(w):
                        w_in_Forest = True
                        root_of_w = tree_to_root[tree_number]
                        tree_num_of_w = tree_number
                        tree_of_w = F[tree_num_of_w]
                        break  # Break the outer for loop

                if not w_in_Forest:
                    # w is matched, so add e and w's matched edge to F
                    F[tree_num_of_v].add_edge(e[0], e[1])  # edge {v,w}
                    # Note: we don't add w to forest nodes b/c it's odd dist from root
                    edge_w = list(M.edges(w))[0]  # get edge {w,x}
                    F[tree_num_of_v].add_edge(edge_w[0], edge_w[1])  # add edge{w,x}
                    F_vertices.append(edge_w[1])  # add {x} to the list of forest nodes

                else:  # w is in Forest
                    # if odd, do nothing.
                    if dist_to_root(w, root_of_w, F[tree_num_of_w]) % 2 == 0:
                        if tree_num_of_v != tree_num_of_w:
                            # returns Shortest path from root(v)--->v-->w---->root(w)
                            path_in_v = nx.shortest_path(F[tree_num_of_v], source=root_of_v, target=v)
                            path_in_w = nx.shortest_path(F[tree_num_of_w], source=w, target=root_of_w)
                            return path_in_v + path_in_w

                        else:  # Contract the blossom
                            # create blossom
                            blossom = nx.shortest_path(tree_of_w, source=v, target=w)
                            blossom.append(v)
                            blossom_nodes = blossom[0:len(blossom) - 1]
                            blossom_set = set(blossom_nodes)
                            # contract blossom into single node w
                            contracted_G = copy.deepcopy(G)
                            for node in blossom_nodes:
                                if node != w:
                                    contracted_G = nx.contracted_nodes(contracted_G, w, node, self_loops=False)

                            # contract blossom's matching: internal matched pairs are
                            # absorbed, but the base's external match (if any) must be
                            # preserved by re-pointing it at the merged vertex w
                            contracted_M = copy.deepcopy(M)
                            external_partner = None
                            for node in blossom_nodes:
                                if contracted_M.has_node(node):
                                    neighbors = list(contracted_M.neighbors(node))
                                    if neighbors and neighbors[0] not in blossom_set:
                                        external_partner = neighbors[0]
                            for node in blossom_nodes:
                                if contracted_M.has_node(node):
                                    contracted_M.remove_node(node)
                            if external_partner is not None:
                                contracted_M.add_edge(w, external_partner)

                            # add blossom to our stack
                            Blossom_stack.append(w)

                            # recurse
                            aug_path = find_augmenting_path(contracted_G, contracted_M, Blossom_stack)

                            # check if blossom exists in aug_path
                            v_B = Blossom_stack.pop()
                            if v_B in aug_path:
                                # Define the L_stem and R_stem
                                L_stem = aug_path[0:aug_path.index(v_B)]
                                R_stem = aug_path[aug_path.index(v_B) + 1:]
                                lifted_blossom = []  # stores the path within the blossom to take
                                # Find base of blossom
                                i = 0
                                base = None
                                base_idx = -1
                                blossom_ext = blossom + [blossom[1]]
                                while base is None and i < len(blossom) - 1:
                                    if not M.has_edge(blossom[i], blossom[i + 1]):
                                        if not M.has_edge(blossom[i + 1], blossom_ext[i + 2]):
                                            base = blossom[i + 1]
                                            base_idx = i + 1
                                        else:
                                            i += 2
                                    else:
                                        i += 1

                                # if needed, create list of blossom nodes starting at base
                                if blossom[0] != base:
                                    based_blossom = []
                                    base_idx = blossom.index(base)
                                    for i in range(base_idx, len(blossom) - 1):
                                        based_blossom.append(blossom[i])
                                    for i in range(0, base_idx):
                                        based_blossom.append(blossom[i])
                                    based_blossom.append(base)
                                else:
                                    based_blossom = blossom

                                # CHECK IF BLOSSOM IS ENDPT
                                if L_stem == [] or R_stem == []:
                                    if L_stem != []:
                                        if G.has_edge(base, L_stem[-1]):
                                            # CASE 1: Chuck the blossom
                                            return L_stem + [base]
                                        else:
                                            # CASE 2: find where L_stem is connected
                                            i = 1
                                            while lifted_blossom == []:
                                                if G.has_edge(based_blossom[i], L_stem[-1]):
                                                    # make sure we're adding the even part to lifted path
                                                    if i % 2 == 0:  # same dir path
                                                        lifted_blossom = list(reversed(based_blossom))[-i - 1:]
                                                    else:  # opposite dir path
                                                        lifted_blossom = based_blossom[i:]
                                                i += 1
                                            return L_stem + lifted_blossom

                                    else:
                                        if G.has_edge(base, R_stem[0]):
                                            # CASE 1: Chuck the blossom
                                            return [base] + R_stem
                                        else:
                                            # CASE 2: find where R_stem is connected
                                            i = 1
                                            while lifted_blossom == []:
                                                if G.has_edge(based_blossom[i], R_stem[0]):
                                                    # make sure we're adding the even part to lifted path
                                                    if i % 2 == 0:  # same dir path
                                                        lifted_blossom = based_blossom[:i + 1]
                                                    else:  # opposite dir path
                                                        lifted_blossom = list(reversed(based_blossom))[:-i]
                                                i += 1
                                            return lifted_blossom + R_stem

                                else:  # blossom is in the middle
                                    # LIFT the blossom
                                    # check if L_stem attaches to base
                                    if M.has_edge(base, L_stem[-1]):
                                        # find where right stem attaches
                                        if G.has_edge(base, R_stem[0]):
                                            # blossom is useless
                                            return L_stem + [base] + R_stem
                                        else:
                                            # blossom needs to be lifted
                                            i = 1
                                            while lifted_blossom == []:
                                                if G.has_edge(based_blossom[i], R_stem[0]):
                                                    # make sure we're adding the even part to lifted path
                                                    if i % 2 == 0:  # same dir path
                                                        lifted_blossom = based_blossom[:i + 1]
                                                    else:  # opposite dir path
                                                        lifted_blossom = list(reversed(based_blossom))[:-i]
                                                i += 1
                                            return L_stem + lifted_blossom + R_stem
                                    else:
                                        # R stem to base is in matching
                                        # check where left stem attaches
                                        if G.has_edge(base, L_stem[-1]):
                                            # blossom is useless
                                            return L_stem + [base] + R_stem
                                        else:
                                            # blossom needs to be lifted
                                            i = 1
                                            while lifted_blossom == []:
                                                if G.has_edge(based_blossom[i], L_stem[-1]):
                                                    # make sure we're adding the even part to lifted path
                                                    if i % 2 == 0:  # same dir path
                                                        lifted_blossom = list(reversed(based_blossom))[-i - 1:]
                                                    else:  # opposite dir path
                                                        lifted_blossom = based_blossom[i:]
                                                i += 1
                                            return L_stem + list(lifted_blossom) + R_stem
                            else:  # blossom is not in aug_path
                                return aug_path
    # If nothing is found
    return P  # Empty path


# faster way to find matchings using networkx
def find_augmenting_path_max_matching(G, M, Blossom_stack=None):
    M_star = nx.max_weight_matching(G, maxcardinality=True)

    M_edges = {frozenset(e) for e in M.edges()}
    M_star_edges = {frozenset(e) for e in M_star}
    sym_diff = M_edges ^ M_star_edges

    diff_graph = nx.Graph()
    diff_graph.add_edges_from(tuple(e) for e in sym_diff)

    exposed = set(G.nodes()) - set(M.nodes())

    for comp in nx.connected_components(diff_graph):
        sub = diff_graph.subgraph(comp)
        endpoints = [n for n, d in sub.degree() if d == 1]
        if len(endpoints) == 2:
            a, b = endpoints
            if a in exposed and b in exposed:
                return nx.shortest_path(sub, source=a, target=b)

    return []  # M is already a maximum matching


# ============================================================================
# Micali-Vazirani blossom algorithm: phase-based search (SEARCH/BLOSS-AUG/
# FINDPATH/OPEN/base*) per Micali & Vazirani (1980) and Vazirani (2020),
# ported from https://github.com/AlexanderSoloviev/mv-matching
# Note: not fully working, just used to test speed.
# Within 1% of the speed of find_augmenting_path_max_matching
# ============================================================================


# INPUT:  Graph G
# OUTPUT: mate - dictionary such that mate[v] == w iff v and w are matched
#         in a maximum cardinality matching of G
def micali_vazirani_max_matching(G):
    gnodes = list(G.nodes())
    if not gnodes:
        return {}

    INFINITY = len(gnodes) + 1

    UNERASED = False
    ERASED = True

    UNVISITED = False
    VISITED = True

    LEFT = -1
    UNMARKED = 0
    RIGHT = 1

    UNUSED = False
    USED = True

    class Bloom:
        __slots__ = ['peaks', 'base']

    class DfsInfo:
        def __init__(self, s, t, vL, vR, dcv, barrier):
            self.s = s
            self.t = t
            self.vL = vL
            self.vR = vR
            self.dcv = dcv
            self.barrier = barrier

    nodeEvenLevel = {}
    nodeOddLevel = {}
    nodeBloom = {}
    nodePredecessors = {}
    nodeSuccessors = {}
    nodeAnomalies = {}
    nodeCount = {}
    nodeErase = {}
    nodeVisit = {}
    nodeMark = {}
    nodeParent = {}

    bloomNodes = []
    candidates = {}
    bridges = {}

    mate = {}

    def search():
        i = 0

        for v in G.nodes():
            if v not in mate:
                nodeEvenLevel[v] = 0
                candidates[0].append(v)

        augmented = False
        while (i < len(gnodes) + 1) and not augmented:

            if i % 2 == 0:  # level i is even
                for v in candidates[i]:
                    for u in G.neighbors(v):
                        if u == v:
                            continue  # ignore self-loops
                        if mate.get(v) != u and nodeErase[u] == UNERASED:
                            assert mate.get(u) != v
                            if nodeEvenLevel[u] < INFINITY:
                                j = (nodeEvenLevel[u] + nodeEvenLevel[v]) // 2
                                bridges[j].add(tuple(sorted([u, v])))
                            else:
                                if nodeOddLevel[u] == INFINITY:
                                    nodeOddLevel[u] = i + 1
                                if nodeOddLevel[u] == i + 1:
                                    nodeCount[u] += 1
                                    nodePredecessors[u].append(v)
                                    nodeSuccessors[v].append(u)
                                    candidates[i + 1].append(u)
                                elif nodeOddLevel[u] < i:
                                    nodeAnomalies[u].append(v)

            else:  # level i is odd
                for v in candidates[i]:
                    if nodeBloom[v] is None:
                        u = mate[v]
                        if nodeOddLevel[u] < INFINITY:
                            j = (nodeOddLevel[u] + nodeOddLevel[v]) // 2
                            bridges[j].add(tuple(sorted([u, v])))
                        elif nodeEvenLevel[u] == INFINITY:
                            nodePredecessors[u] = [v]
                            nodeSuccessors[v] = [u]
                            nodeCount[u] = 1
                            nodeEvenLevel[u] = i + 1
                            candidates[i + 1].append(u)

            for s, t in bridges[i]:
                if nodeErase[s] == UNERASED and nodeErase[t] == UNERASED:
                    augmented = augmentBlossom(s, t, i)

            i += 1

        return augmented

    def augmentBlossom(s, t, i):
        foundBloom = False
        augmented = False

        vL = baseStar(s) if nodeBloom[s] else s
        vR = baseStar(t) if nodeBloom[t] else t

        if vL == vR:
            return False  # s and t belong to the same compressed bloom

        if nodeBloom[s]:
            nodeParent[vL] = s
        if nodeBloom[t]:
            nodeParent[vR] = t

        nodeMark[vL] = LEFT
        nodeMark[vR] = RIGHT
        bloomNodes.append(vL)
        bloomNodes.append(vR)

        dfsInfo = DfsInfo(s, t, vL, vR, None, vR)

        while not foundBloom and not augmented:

            if dfsInfo.vL is None or dfsInfo.vR is None:
                return False
            level_vL = min(nodeEvenLevel[dfsInfo.vL], nodeOddLevel[dfsInfo.vL])
            level_vR = min(nodeEvenLevel[dfsInfo.vR], nodeOddLevel[dfsInfo.vR])

            if dfsInfo.vL not in mate and dfsInfo.vR not in mate:
                pathL = findPath(dfsInfo.s, dfsInfo.vL, None)
                pathR = findPath(dfsInfo.t, dfsInfo.vR, None)
                path = connectPath(pathL, pathR, dfsInfo.s, dfsInfo.t)
                augmentMatching(dfsInfo.vL, dfsInfo.vR)
                erasePath(path)
                augmented = True
                break
            elif level_vL >= level_vR:
                foundBloom = leftDfs(dfsInfo)
            else:
                foundBloom = rightDfs(dfsInfo)

        if foundBloom and dfsInfo.dcv is not None:

            nodeMark[dfsInfo.dcv] = UNMARKED  # dcv cannot be in the bloom

            b = Bloom()
            b.peaks = (dfsInfo.s, dfsInfo.t)
            b.base = dfsInfo.dcv

            for v in bloomNodes:
                if nodeMark[v] == UNMARKED or nodeBloom[v] is not None:
                    continue  # no mark, or bloom already defined: skip it

                nodeBloom[v] = b

                level_v = min(nodeEvenLevel[v], nodeOddLevel[v])
                if level_v % 2 == 0:  # v is outer
                    nodeOddLevel[v] = 2 * i + 1 - nodeEvenLevel[v]
                else:  # v is inner
                    nodeEvenLevel[v] = 2 * i + 1 - nodeOddLevel[v]
                    candidates[nodeEvenLevel[v]].append(v)
                    for z in nodeAnomalies[v]:
                        j = (nodeEvenLevel[v] + nodeEvenLevel[z]) // 2
                        bridges[j].add(tuple(sorted([v, z])))
                        G[v][z]['use'] = USED

        del bloomNodes[:]

        return augmented

    def connectPath(pathL, pathR, s, t):
        reverseL = True if s == pathL[0] else False
        reverseR = True if t == pathR[-1] else False

        if reverseL:
            nodeParent[pathL[0]] = None
            prevv = None
            currentv = pathL[-1]
            nextv = None
            while currentv is not None:
                nextv = nodeParent[currentv]
                nodeParent[currentv] = prevv
                prevv = currentv
                currentv = nextv

            pathL.reverse()

        if reverseR:
            nodeParent[pathR[0]] = None
            prevv = None
            currentv = pathR[-1]
            nextv = None
            while currentv is not None:
                nextv = nodeParent[currentv]
                nodeParent[currentv] = prevv
                prevv = currentv
                currentv = nextv

            pathR.reverse()

        path = []
        path.extend(pathL)
        path.extend(pathR)

        nodeParent[pathR[0]] = pathL[-1]

        return path

    def augmentMatching(lv, rv):
        firstv = rv
        secondv = None
        while firstv != lv:
            secondv = nodeParent[firstv]

            if mate.get(secondv) != firstv:
                assert mate.get(firstv) != secondv
                mate[firstv] = secondv
                mate[secondv] = firstv

            firstv = secondv

    def leftDfs(dfsInfo):
        for uL in nodePredecessors[dfsInfo.vL]:

            if G[dfsInfo.vL][uL]['use'] == USED or nodeErase[uL] == ERASED:
                continue

            G[dfsInfo.vL][uL]['use'] = USED

            if nodeBloom[uL]:
                uL = baseStar(uL)

            if nodeMark[uL] == UNMARKED:
                nodeMark[uL] = LEFT
                nodeParent[uL] = dfsInfo.vL
                dfsInfo.vL = uL
                bloomNodes.append(uL)
                return False

            elif uL == dfsInfo.vR:
                dfsInfo.dcv = uL

        if dfsInfo.vL == dfsInfo.s:
            return True  # signal discovery of a bloom
        elif nodeParent[dfsInfo.vL] is not None:
            dfsInfo.vL = nodeParent[dfsInfo.vL]  # keep backtracking

        return False

    def rightDfs(dfsInfo):
        for uR in nodePredecessors[dfsInfo.vR]:

            if G[dfsInfo.vR][uR]['use'] == USED or nodeErase[uR] == ERASED:
                continue

            G[dfsInfo.vR][uR]['use'] = USED

            if nodeBloom[uR]:
                uR = baseStar(uR)

            if nodeMark[uR] == UNMARKED:
                nodeMark[uR] = RIGHT
                nodeParent[uR] = dfsInfo.vR
                dfsInfo.vR = uR
                bloomNodes.append(uR)
                return False

            elif uR == dfsInfo.vL:
                dfsInfo.dcv = uR

        if dfsInfo.vR == dfsInfo.barrier:
            dfsInfo.vR = dfsInfo.dcv
            dfsInfo.barrier = dfsInfo.dcv
            nodeMark[dfsInfo.vR] = RIGHT
            if nodeParent[dfsInfo.vL] is not None:
                dfsInfo.vL = nodeParent[dfsInfo.vL]  # force leftDfs to backtrack from vL = dcv
        elif nodeParent[dfsInfo.vR] is not None:
            dfsInfo.vR = nodeParent[dfsInfo.vR]  # keep backtracking

        return False

    def erasePath(path):
        while path:
            y = path.pop()
            nodeErase[y] = ERASED

            for z in nodeSuccessors[y]:
                if nodeErase[z] == UNERASED:
                    nodeCount[z] -= 1

                    if nodeCount[z] == 0:
                        path.append(z)

    def findPath(high, low, b):
        level_high = min(nodeEvenLevel[high], nodeOddLevel[high])
        level_low = min(nodeEvenLevel[low], nodeOddLevel[low])
        assert level_high >= level_low

        if high == low:
            return [high]

        path = []

        v = high
        u = high
        while u != low:

            hasUnvisitedPredecessor = False

            for p in nodePredecessors[v]:
                if G[p][v]['visit'] == UNVISITED:
                    hasUnvisitedPredecessor = True

                    if nodeBloom[v] is None or nodeBloom[v] == b:
                        G[p][v]['visit'] = VISITED
                        u = p
                    else:
                        u = nodeBloom[v].base

                    break

            if not hasUnvisitedPredecessor:
                assert nodeParent[v] is not None
                v = nodeParent[v]
            else:
                level_u = min(nodeEvenLevel[u], nodeOddLevel[u])

                if nodeErase[u] == UNERASED and level_u >= level_low \
                and (u == low or (nodeVisit[u] == UNVISITED
                and (nodeMark[u] == nodeMark[high] != UNMARKED
                or (nodeBloom[u] is not None and nodeBloom[u] != b)))):
                    nodeVisit[u] = VISITED
                    nodeParent[u] = v
                    v = u

        while u != high:
            path.append(u)
            u = nodeParent[u]
        path.append(u)
        path.reverse()

        # blooms other than b remain to be opened via openBloom
        j = 0
        while j < len(path) - 1:
            xj = path[j]

            if nodeBloom[xj] is not None and nodeBloom[xj] != b:
                nodeVisit[xj] = UNVISITED
                path[j: j + 2], pathLength = openBloom(xj)
                nodeParent[xj] = path[j - 1] if j > 0 else None
                j += pathLength - 1
            j += 1

        return path

    def openBloom(x):
        bloom = nodeBloom[x]
        base = bloom.base
        level_x = min(nodeEvenLevel[x], nodeOddLevel[x])
        path = []

        if level_x % 2 == 0:  # x is outer
            path = findPath(x, base, bloom)
        else:  # x is inner
            (leftPeak, rightPeak) = bloom.peaks
            if nodeMark[x] == LEFT:
                pathLeft = findPath(leftPeak, x, bloom)
                pathRight = findPath(rightPeak, base, bloom)
                path = connectPath(pathLeft, pathRight, leftPeak, rightPeak)
            elif nodeMark[x] == RIGHT:
                pathLeft = findPath(rightPeak, x, bloom)
                pathRight = findPath(leftPeak, base, bloom)
                path = connectPath(pathLeft, pathRight, rightPeak, leftPeak)
        return (path, len(path))

    def baseStar(v):
        base = v
        while nodeBloom[base] is not None:
            assert nodeBloom[base].base != base
            base = nodeBloom[base].base
        return base

    # Main loop: iterate phases until no more augmentation is possible
    augmented = True
    while augmented:

        for v in G.nodes():
            nodeEvenLevel[v] = INFINITY
            nodeOddLevel[v] = INFINITY
            nodeBloom[v] = None
            nodePredecessors[v] = []
            nodeSuccessors[v] = []
            nodeAnomalies[v] = []
            nodeCount[v] = 0
            nodeErase[v] = UNERASED
            nodeVisit[v] = UNVISITED
            nodeMark[v] = UNMARKED
            nodeParent[v] = None

        for u, v, d in G.edges(data=True):
            if u == v:
                continue  # ignore self-loops
            d['use'] = UNUSED
            d['visit'] = UNVISITED

        for i in range(len(gnodes) + 1):
            candidates[i] = []
            bridges[i] = set()

        augmented = search()

        for v in mate:
            assert mate[mate[v]] == v

    for u, v, d in G.edges(data=True):
        if u == v:
            continue
        del d['use']
        del d['visit']

    return mate


# INPUT:  Graph G, current matching M (an nx.Graph on a subset of G's edges)
# OUTPUT: a single augmenting path P (list of vertices) w.r.t. M, found by
#         diffing M against a fresh Micali-Vazirani solve of G, or [] if M
#         is already a maximum matching
def find_augmenting_path_micali_vazirani(G, M, Blossom_stack=None):
    mv_mate = micali_vazirani_max_matching(G)

    M_edges = {frozenset(e) for e in M.edges()}
    M_star_edges = {frozenset((v, w)) for v, w in mv_mate.items() if v < w}
    sym_diff = M_edges ^ M_star_edges

    diff_graph = nx.Graph()
    diff_graph.add_edges_from(tuple(e) for e in sym_diff)

    exposed = set(G.nodes()) - set(M.nodes())

    for comp in nx.connected_components(diff_graph):
        sub = diff_graph.subgraph(comp)
        endpoints = [n for n, d in sub.degree() if d == 1]
        if len(endpoints) == 2:
            a, b = endpoints
            if a in exposed and b in exposed:
                return nx.shortest_path(sub, source=a, target=b)

    return []  # M is already a maximum matching



# ============================================================================
# Determines winner in AAC from a starting vertex v
# Does removing a vertex change the maximum matching size?
# Returns matching, 'P1' or 'P2'
# ============================================================================

def AAC_winner(G, M, v):
    G_no_v, M_no_v = G.copy(), M.copy()
    G_no_v.remove_node(v)

    res = find_maximum_matching(G, M).number_of_edges()
    res_no_v = find_maximum_matching(G_no_v, M_no_v).number_of_edges()

    if res == res_no_v:
        return M, 'P2'  # P2 win
    else:
        return M, 'P1'  # P1 win
