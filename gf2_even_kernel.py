from itertools import product


# ============================================================================
# Even kernels via linear algebra over GF(2).
#
# An "even kernel" is a set S of vertices such that
#   (1) S is independent: no vertex in S is adjacent to another vertex in S,
#   (2) every vertex NOT in S has an EVEN number of neighbors in S.
#
# Writing x_v = 1 if v is in S and 0 otherwise: condition (2) says the sum of
# x_w over the neighbors w of v is 0 mod 2 for v outside S, and condition (1)
# makes that sum exactly 0 for v inside S. So every even kernel solves the
# homogeneous system
#
#       A x = 0   (mod 2)        (A = adjacency matrix of G)
#
# The converse fails: a null-space vector may put two adjacent vertices in S
# (each then sees an even but NONZERO number of S-neighbors, violating (1)).
# Independence is not a linear condition, so the null space only prunes the
# search: we row-reduce A to RREF with mod-2 arithmetic (over GF(2) "add" and
# "subtract" are both just XOR), read off a null-space basis, enumerate its
# 2^dim combinations instead of all 2^N subsets, and keep the solutions whose
# support is independent. Those are exactly the even kernels.
# ============================================================================


# adjacency matrix of G over GF(2), as a list of 0/1 rows.
# nodes fixes the row/column order (defaults to sorted node labels).
def adjacency_matrix_gf2(G, nodes=None):
    if nodes is None:
        nodes = sorted(G.nodes())
    idx = {u: i for i, u in enumerate(nodes)}
    N = len(nodes)
    A = [[0] * N for _ in range(N)]
    for u in nodes:
        for w in G.neighbors(u):
            A[idx[u]][idx[w]] = 1
    return A, nodes, idx


# reduce M to RREF over GF(2). Returns (R, pivots) where R is the reduced
# matrix and pivots maps {pivot column -> its row index in R}.
def rref_gf2(M):
    R = [row[:] for row in M]
    nrows = len(R)
    ncols = len(R[0]) if R else 0
    pivots = {}
    r = 0
    for c in range(ncols):
        # find a row at or below r with a 1 in column c
        piv = next((rr for rr in range(r, nrows) if R[rr][c] == 1), None)
        if piv is None:
            continue
        R[r], R[piv] = R[piv], R[r]           # move it into pivot position
        for rr in range(nrows):               # clear the rest of the column
            if rr != r and R[rr][c] == 1:
                R[rr] = [a ^ b for a, b in zip(R[rr], R[r])]
        pivots[c] = r
        r += 1
    return R, pivots


# basis for the null space of M over GF(2): one vector per free column, by
# setting that free var to 1, the rest to 0, and back-substituting the pivots.
def null_space_basis(M):
    R, pivots = rref_gf2(M)
    N = len(M[0]) if M else 0
    free = [c for c in range(N) if c not in pivots]
    basis = []
    for fc in free:
        x = [0] * N
        x[fc] = 1
        for c, rrow in pivots.items():
            # pivot row: x_c + (free terms) = 0  ->  x_c = sum of free terms
            x[c] = 0
            for j in free:
                x[c] ^= R[rrow][j] & x[j]
        basis.append(x)
    return basis, pivots, free


# no two vertices of S are adjacent?
def is_independent(G, S):
    Sset = set(S)
    return not any(w in Sset for u in Sset for w in G.neighbors(u))


# S is independent, and every vertex outside S has an even number of
# neighbors in S?
def is_even_kernel(G, S):
    Sset = set(S)
    if not is_independent(G, Sset):
        return False
    return all(
        sum(1 for w in G.neighbors(u) if w in Sset) % 2 == 0
        for u in G.nodes() if u not in Sset
    )



    A, nodes, _ = adjacency_matrix_gf2(G, nodes)
    basis, _, _ = null_space_basis(A)
    return [[nodes[i] for i, b in enumerate(v) if b] for v in basis], nodes


# every vertex outside S is adjacent to exactly 0 or 2 vertices in S?
# (stricter than evenness: rules out 4, 6, ... neighbors in S)
def has_zero_or_two_neighbors(G, S):
    Sset = set(S)
    return all(
        sum(1 for w in G.neighbors(u) if w in Sset) in (0, 2)
        for u in G.nodes() if u not in Sset
    )


# every even kernel: XOR all 2^(#basis) combinations of the null-space basis,
# keep the ones whose support is independent (evenness outside S is already
# guaranteed by A x = 0). include_empty=False drops the trivial empty kernel.
# zero_or_two=True keeps only kernels where each vertex outside S has exactly
# 0 or 2 neighbors in S.
def all_even_kernels(G, nodes=None, include_empty=False, zero_or_two=False):
    A, nodes, _ = adjacency_matrix_gf2(G, nodes)
    basis, _, _ = null_space_basis(A)
    N = len(nodes)
    kernels = []
    for coeffs in product((0, 1), repeat=len(basis)):
        x = [0] * N
        for c, vec in zip(coeffs, basis):
            if c:
                x = [a ^ b for a, b in zip(x, vec)]
        S = [nodes[i] for i, b in enumerate(x) if b]
        if not (S or include_empty) or not is_independent(G, S):
            continue
        if zero_or_two and not has_zero_or_two_neighbors(G, S):
            continue
        kernels.append(S)
    return kernels, nodes


# print the T3-style walkthrough: index map, per-vertex equations, the RREF,
# the pivot equations, the free variables, and each basis kernel verified.
def walkthrough(G, nodes=None, name="G"):
    A, nodes, idx = adjacency_matrix_gf2(G, nodes)
    N = len(nodes)

    print(f"===== even kernels of {name} over GF(2) =====\n")

    print("index -> vertex")
    for u in nodes:
        print(f"  x{idx[u]} = {u}")
    print()

    print("Equations (row = vertex, sum of listed vars = 0 mod 2):")
    for i, u in enumerate(nodes):
        terms = " + ".join(f"x{j}" for j in range(N) if A[i][j]) or "0"
        print(f"  Eq{i} [{u}]: {terms} = 0")
    print()

    R, pivots = rref_gf2(A)
    print("RREF of the adjacency matrix (zero rows dropped):")
    for row in R:
        if any(row):
            print("  " + " ".join(str(v) for v in row))
    print()

    free = [c for c in range(N) if c not in pivots]
    rank = len(pivots)
    print(f"rank = {rank},  free variables = {N - rank}")
    print("pivot columns:", sorted(pivots))
    print("free columns :", free)
    print()

    print("Pivot equations (each pivot var in terms of the free vars):")
    for c in sorted(pivots):
        row = R[pivots[c]]
        rhs = " + ".join(f"x{j}" for j in free if row[j]) or "0"
        print(f"  x{c} = {rhs}")
    print("  free:", ", ".join(f"x{j}" for j in free) or "(none)")
    print()

    basis, _, _ = null_space_basis(A)
    print(f"null-space basis ({len(basis)} vector(s)) -> candidate kernels:")
    if not basis:
        print("  null space is trivial: only the empty kernel exists")
    for v in basis:
        S = [nodes[i] for i, b in enumerate(v) if b]
        print(f"  {v}")
        print(f"    S = {S}")
        print(f"    independent? {is_independent(G, S)}")
    print()

    kernels, _ = all_even_kernels(G, nodes)
    print(f"even kernels: {len(kernels)} of the {2 ** len(basis) - 1} nonempty "
          f"null-space solutions are independent:")
    for S in kernels:
        print(f"  S = {S}")
        print(f"    verified even kernel? {is_even_kernel(G, S)}")


# draw every nonempty even kernel, capped at max_panels panels.
# layout=None guesses from the node labels; see visualize.LAYOUTS.
def visualize_even_kernels(G, nodes=None, layout=None, name="G", max_panels=16):
    from visualize import visualize_kernels

    kernels, nodes = all_even_kernels(G, nodes)
    if len(kernels) > max_panels:
        name = f"{name} — first {max_panels} of {len(kernels)} kernels"
        kernels = kernels[:max_panels]
    return visualize_kernels(G, kernels, layout=layout, name=name)


    G = build_graph(prism_graph_nodes(n), prism_graph_adjacency_listing(n))
    walkthrough(G, name="prism n={n}")
    visualize_even_kernels(G, name="prism n={n}")
    #
    # G = build_graph(cycle_graph_nodes(5), cycle_graph_adjacency_listing(5))
    # walkthrough(G, name="cycle n=5")
    # visualize_even_kernels(G, name="cycle n=5")
