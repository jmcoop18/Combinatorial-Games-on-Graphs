# Nimber calculator for combinatorial games on graphs

Computer code for playing the combinatorial games <i>Make-A-Cycle</i> (MAC) and <i>Avoid-A-Cycle</i> (AAC). These games were first defined for Cayley graphs in the paper [Relator Games on Groups](http://dx.doi.org/10.1515/9783110755411-011). A second paper, [Cycle Games on Graphs](https://math.colgate.edu/~integers/yg4/yg4.pdf), discusses the MAC and AAC games on additional graphs including complete and complete bipartite graphs, wheel graphs, stacked prism graphs, and some generalized Petersen graphs.

## Algorithms Used

For a starting vertex v, `find_nimber` determines the AAC winner from v (via `AAC_winner`), then recurses on each connected vertex of v with v removed from the graph, then combining the child nimbers with the mex (minimum excluded value) and working back up the game tree to get the nimber.

`AAC_winner` decides the winner by comparing the size of a maximum matching on G against the size of a maximum matching on G with v removed. If they're equal, player 2 wins, otherwise player 1 wins. Both matchings are computed with `find_maximum_matching`, which repeatedly finds an augmenting path and augments the matching along it until none remain (Edmonds' blossom algorithm).


## Running the code/ Project structure

### Setup

```
pip install -r requirements.txt
```

### Usage

```
python cli.py
```

The CLI is menu-driven. Pick a graph type first, then a run mode:

**Graph types:** Prism, Triangular Grid, Path, Cycle, Wheel, Complete Split, or a Custom Adjacency Listing (typed/pasted in as `i,j` pairs).

**Run modes:**
- Single run — fixed graph size, fixed starting vertex
- Iterate over all vertices — fixed graph size, prints the nimber from every vertex
- Iterate over a range of sizes — fixed starting vertex, sweeps the graph size (for Complete Split graphs, this instead sweeps both m and n)

Depending on your choices, you'll be prompted for the graph size(s) and a starting vertex. Note that vertices are `layer,index` pairs (e.g. `0,3`) for Prism and Triangular Grid graphs, and plain integers for everything else.

### Project structure

| File | Purpose |
|---|---|
| `cli.py` | Menu-driven entry point for running the tool |
| `graphs.py` | Builds prism, triangular grid, path, cycle, wheel, and complete split graphs, plus custom adjacency listings |
| `matching.py` | Maximum matching (Edmonds' blossom algorithm) and AAC win determination |
| `nimber.py` | Recursive nimber computation on top of `matching.py` |
| `Adjacency_Listings/` | Saved adjacency listings for specific graph instances |

