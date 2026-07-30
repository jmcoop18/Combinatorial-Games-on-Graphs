# Nimber calculator for combinatorial games on graphs

Computer code for playing the combinatorial games <i>Make-A-Cycle</i> (MAC) and <i>Avoid-A-Cycle</i> (AAC). These games were first defined for Cayley graphs in the paper [Relator Games on Groups](http://dx.doi.org/10.1515/9783110755411-011). A second paper, [Cycle Games on Graphs](https://math.colgate.edu/~integers/yg4/yg4.pdf), discusses the MAC and AAC games on additional graphs including complete and complete bipartite graphs, wheel graphs, stacked prism graphs, and some generalized Petersen graphs.

## Algorithms Used

### AAC

For a starting vertex v, `blossomX_AAC_nimber` (and its pure-networkx counterpart `nx_AAC_nimber`) decides the winner from v, and if player 1 wins, recurses on each neighbor of v with v removed from the graph, combining the child nimbers with the mex (minimum excluded value) and working back up the game tree to get the nimber. Both cache nimbers and matching sizes keyed on `(subgraph, vertex)` so repeated positions are never recomputed.

The winner is decided by comparing the size of a maximum matching on G against the size of a maximum matching on G with v removed: if they're equal, player 2 wins (nimber 0, and the subtree is pruned); otherwise player 1 wins. `blossomX_AAC_nimber` gets those matching sizes from the Rust `xblossom` extension via `rust_matching.py` for speed, with a transparent networkx fallback if the extension isn't built; `nx_AAC_nimber` uses networkx directly. `matching.py` holds a from-scratch implementation of the same idea — `find_maximum_matching` repeatedly finds an augmenting path and augments the matching along it until none remain (Edmonds' blossom algorithm), and `AAC_winner` wraps the matching-size comparison — kept as a readable baseline.

For complete multipartite graphs, `multipartite_AAC_nimber` skips matching-based recursion entirely in favor of a closed-form matching-size formula, since the matching size of K(n1,...,nk) is known directly from the part sizes.

### MAC

`bitmask_MAC_nimber` plays out the same mex-of-children recursion, but since a MAC move removes an edge rather than a vertex, the graph is packed into integer bitmasks (one bitmask of neighbors per vertex, plus a bitmask of visited vertices) instead of copying a networkx `Graph` on every move. This makes the memo key `(adjacency, vertex, seen_mask)` cheap to build and hash, so caching actually pays off at the sizes explored here.

### Even kernels

`gf2_even_kernel.py` finds even kernels (independent sets where every outside vertex has an even number of neighbors inside the set) by solving `Ax = 0` over GF(2), where A is the adjacency matrix, then filtering the null space down to solutions that are also independent sets.

## Running the code/ Project structure

### Setup

networkx==3.6.1  
Python==3.13.7

(Optional, for faster matchings) Rust + [maturin](https://github.com/PyO3/maturin), then `cd xblossom && maturin develop --release`. Everything falls back to plain networkx if this isn't built.

### Usage

```
python cli.py
```

The CLI is menu-driven. Pick an algorithm first (Nimbers for AAC, Nimbers for MAC, or Even Kernels), then a graph type, then a run mode.

**Graph types:** Prism, Path, Cycle, Wheel, Generalized Wheel, Triangular Grid, Rectangular Grid, Complete, Complete Split, Complete K-partite, or a Custom Adjacency Listing (typed/pasted in as `i,j` pairs).

**Run modes:**
- Single run — fixed graph size, fixed starting vertex
- Iterate over all vertices — fixed graph size, prints the nimber from every vertex
- Iterate over a range of sizes — fixed starting vertex, sweeps the graph size (for Generalized Wheel and Complete Split graphs, this instead sweeps both m and n)

Depending on your choices, you'll be prompted for the graph size(s) and a starting vertex. Note that vertices are `layer,index` pairs (e.g. `0,3`) for Prism and Triangular Grid graphs, and plain integers for everything else.

Press Esc at any prompt to exit immediately, or `r` at the main menu to replay the previous run.

Running `python cli.py sweep <k>` (instead of opening the menu) sweeps AAC nimbers over small complete k-partite graphs, for `k` parts.

### Project structure

| File | Purpose |
|---|---|
| `cli.py` | Menu-driven entry point for running the tool |
| `graphs.py` | Builds prism, path, cycle, wheel, generalized wheel, triangular/rectangular grid, complete, complete split, and complete k-partite graphs, plus custom adjacency listings |
| `matching.py` | From-scratch maximum matching (Edmonds' blossom, plus a Micali-Vazirani variant used for speed comparisons) and AAC win determination; a readable baseline, kept alongside the faster `rust_matching.py` path |
| `rust_matching.py` | Drop-in matching-size/maximum-matching functions backed by the Rust `xblossom` extension, falling back to networkx if it isn't built |
| `xblossom/` | Rust implementation of blossom matching, built via maturin and called from `rust_matching.py` |
| `nimber.py` | Nimber computation for AAC and MAC on top of `matching.py`, plus the closed-form complete-multipartite solver |
| `gf2_even_kernel.py` | Even kernel search via linear algebra over GF(2) |
| `even_kernels.py` | Earlier, incomplete even-kernel approach; superseded by `gf2_even_kernel.py` |
| `old_functions.py` | Earlier nimber implementations kept for reference/documentation, not used by the CLI |
| `visualize.py` | Shared graph-drawing helpers (node layouts per graph family, even-kernel figures) |
| `Adjacency_Listings/` | Saved adjacency listings for specific graph instances |

