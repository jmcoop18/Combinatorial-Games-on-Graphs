// Edmonds' blossom algorithm: maximum cardinality matching on a general
// (non-bipartite) undirected graph, O(V^3).
//
// Output follows X-Blossom's convention: M[v] = matched partner of v, or -1.
//
// Structure of one phase, mirroring X-Blossom's decomposition:
//   1. collect exposed (unmatched) nodes            (parExposedNode)
//   2. search for an augmenting path from each root (parFindAugmentingPath...)
//      contracting any odd cycle (blossom) found along the way
//   3. flip the path to grow the matching by one    (parNewMatchingVector)
// The serial kernel below does the same three steps one root at a time.
// X-Blossom parallelizes step 2 across roots with an atomic path table;
// that is the extension point if this ever needs threads (see
// `maximum_matching`'s `num_threads` parameter, currently accepted but unused).

use crate::graph::Graph;
use std::collections::VecDeque;

const UNMATCHED: i64 = -1;

// state for one augmenting-path search (one BFS tree rooted at an exposed node)
struct Search {
    // parent[v]: previous vertex on the alternating path into v (odd levels), or -1
    parent: Vec<i64>,
    // base[v]: base vertex of the contracted blossom containing v (v itself if none)
    base: Vec<usize>,
    // in_queue[v]: v has been enqueued as an even-level vertex
    in_queue: Vec<bool>,
    queue: VecDeque<usize>,
}

impl Search {
    fn new(n: usize) -> Self {
        Search {
            parent: vec![-1; n],
            base: (0..n).collect(),
            in_queue: vec![false; n],
            queue: VecDeque::new(),
        }
    }

    fn reset(&mut self, root: usize) {
        let n = self.base.len();
        self.parent.iter_mut().for_each(|p| *p = -1);
        for (v, b) in self.base.iter_mut().enumerate() {
            *b = v;
        }
        self.in_queue.iter_mut().for_each(|q| *q = false);
        self.queue.clear();
        self.in_queue[root] = true;
        self.queue.push_back(root);
        debug_assert!(root < n);
    }
}

// lowest common ancestor of the blossom bases of a and b in the alternating tree
fn lowest_common_base(s: &Search, mate: &[i64], mut a: usize, mut b: usize) -> usize {
    let mut on_path = vec![false; s.base.len()];
    // walk a up to the root, marking bases
    loop {
        a = s.base[a];
        on_path[a] = true;
        if mate[a] == UNMATCHED {
            break; // reached the root
        }
        let p = s.parent[mate[a] as usize];
        if p == -1 {
            break;
        }
        a = p as usize;
    }
    // walk b up until we hit a marked base
    loop {
        b = s.base[b];
        if on_path[b] {
            return b;
        }
        b = s.parent[mate[b] as usize] as usize;
    }
}

// mark blossom bases on the path from v down to the blossom base `bottom`,
// and re-point parents so the contracted blossom can later be traversed
// in either direction (this is the "lifting" bookkeeping)
fn mark_path(
    s: &mut Search,
    mate: &[i64],
    in_blossom: &mut [bool],
    mut v: usize,
    bottom: usize,
    mut child: usize,
) {
    while s.base[v] != bottom {
        in_blossom[s.base[v]] = true;
        let m = mate[v] as usize;
        in_blossom[s.base[m]] = true;
        s.parent[v] = child as i64;
        child = m;
        v = s.parent[m] as usize;
    }
}

// grow the matching by one edge if an augmenting path from `root` exists
fn augment_from(g: &Graph, mate: &mut [i64], s: &mut Search, root: usize) -> bool {
    let n = g.num_nodes();
    s.reset(root);

    while let Some(v) = s.queue.pop_front() {
        for &to in g.neighbors(v) {
            // skip edges inside a contracted blossom and the matched edge we came by
            if s.base[v] == s.base[to] || mate[v] == to as i64 {
                continue;
            }
            if to == root || (mate[to] != UNMATCHED && s.parent[mate[to] as usize] != -1) {
                // `to` is an even-level vertex: the edge (v, to) closes an odd
                // cycle. Contract the blossom to its base.
                let bottom = lowest_common_base(s, mate, v, to);
                let mut in_blossom = vec![false; n];
                mark_path(s, mate, &mut in_blossom, v, bottom, to);
                mark_path(s, mate, &mut in_blossom, to, bottom, v);
                for i in 0..n {
                    if in_blossom[s.base[i]] {
                        s.base[i] = bottom;
                        if !s.in_queue[i] {
                            s.in_queue[i] = true;
                            s.queue.push_back(i);
                        }
                    }
                }
            } else if s.parent[to] == -1 {
                // `to` is unvisited: extend the alternating tree
                s.parent[to] = v as i64;
                if mate[to] == UNMATCHED {
                    // augmenting path found: flip matched/unmatched along it
                    let mut u = to;
                    loop {
                        let pv = s.parent[u] as usize;
                        let next = mate[pv];
                        mate[u] = pv as i64;
                        mate[pv] = u as i64;
                        if next == UNMATCHED {
                            return true;
                        }
                        u = next as usize;
                    }
                } else {
                    // follow the matched edge; its endpoint becomes even-level
                    let m = mate[to] as usize;
                    s.in_queue[m] = true;
                    s.queue.push_back(m);
                }
            }
        }
    }
    false
}

// Maximum cardinality matching. `_num_threads` mirrors X-Blossom's API and is
// the hook for a future parallel phase; the current kernel is serial.
pub fn maximum_matching(g: &Graph, _num_threads: usize) -> Vec<i64> {
    let n = g.num_nodes();
    let mut mate: Vec<i64> = vec![UNMATCHED; n];

    // greedy warm start: cheap, and skips most augmenting-path searches
    for v in 0..n {
        if mate[v] == UNMATCHED {
            for &u in g.neighbors(v) {
                if mate[u] == UNMATCHED && u != v {
                    mate[v] = u as i64;
                    mate[u] = v as i64;
                    break;
                }
            }
        }
    }

    let mut s = Search::new(n);
    for v in 0..n {
        if mate[v] == UNMATCHED {
            augment_from(g, &mut mate, &mut s, v);
        }
    }
    mate
}

pub fn matching_size(mate: &[i64]) -> usize {
    mate.iter().filter(|&&m| m != UNMATCHED).count() / 2
}

// validates M: symmetric, in-range, partners actually adjacent
pub fn test_matching(g: &Graph, mate: &[i64]) -> Result<(), String> {
    let n = g.num_nodes();
    if mate.len() != n {
        return Err(format!("matching has length {} for {} nodes", mate.len(), n));
    }
    for v in 0..n {
        let m = mate[v];
        if m == UNMATCHED {
            continue;
        }
        let m = m as usize;
        if m >= n {
            return Err(format!("M[{v}] = {m} out of range"));
        }
        if mate[m] != v as i64 {
            return Err(format!("asymmetric: M[{v}] = {m} but M[{m}] = {}", mate[m]));
        }
        if !g.neighbors(v).contains(&m) {
            return Err(format!("M[{v}] = {m} but ({v}, {m}) is not an edge"));
        }
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    fn size_of(num_nodes: usize, edges: &[(usize, usize)]) -> usize {
        let g = Graph::from_edges(num_nodes, edges).unwrap();
        let mate = maximum_matching(&g, 1);
        test_matching(&g, &mate).unwrap();
        matching_size(&mate)
    }

    #[test]
    fn empty_and_trivial() {
        assert_eq!(size_of(0, &[]), 0);
        assert_eq!(size_of(1, &[]), 0);
        assert_eq!(size_of(2, &[(0, 1)]), 1);
    }

    #[test]
    fn odd_cycles() {
        // triangle: one edge matched, one vertex exposed
        assert_eq!(size_of(3, &[(0, 1), (1, 2), (2, 0)]), 1);
        // C5
        assert_eq!(size_of(5, &[(0, 1), (1, 2), (2, 3), (3, 4), (4, 0)]), 2);
        // C7
        let c7: Vec<_> = (0..7).map(|i| (i, (i + 1) % 7)).collect();
        assert_eq!(size_of(7, &c7), 3);
    }

    #[test]
    fn paths() {
        assert_eq!(size_of(4, &[(0, 1), (1, 2), (2, 3)]), 2);
        assert_eq!(size_of(5, &[(0, 1), (1, 2), (2, 3), (3, 4)]), 2);
    }

    #[test]
    fn blossom_forces_augmentation() {
        // Classic case a greedy/bipartite approach gets wrong: a triangle
        // with two pendant vertices. Perfect matching exists (size 2)
        // only if the search can flip through the odd cycle.
        //   3 - 0 - 1 - 4   plus edges (0,2), (1,2)
        assert_eq!(size_of(5, &[(0, 1), (1, 2), (2, 0), (0, 3), (1, 4)]), 2);
    }

    #[test]
    fn petersen_graph() {
        // 3-regular, 10 nodes, has a perfect matching
        let edges = [
            (0, 1), (1, 2), (2, 3), (3, 4), (4, 0), // outer C5
            (5, 7), (7, 9), (9, 6), (6, 8), (8, 5), // inner pentagram
            (0, 5), (1, 6), (2, 7), (3, 8), (4, 9), // spokes
        ];
        assert_eq!(size_of(10, &edges), 5);
    }

    #[test]
    fn complete_graphs() {
        for n in 1..=9 {
            let mut edges = vec![];
            for u in 0..n {
                for v in (u + 1)..n {
                    edges.push((u, v));
                }
            }
            assert_eq!(size_of(n, &edges), n / 2, "K_{n}");
        }
    }

    #[test]
    fn disconnected_components() {
        // triangle + single edge + isolated vertex
        assert_eq!(size_of(6, &[(0, 1), (1, 2), (2, 0), (3, 4)]), 2);
    }

    #[test]
    fn random_graphs_match_bruteforce() {
        // deterministic LCG so the test is reproducible
        let mut state: u64 = 0x5eed;
        let mut next = move || {
            state = state.wrapping_mul(6364136223846793005).wrapping_add(1442695040888963407);
            (state >> 33) as usize
        };
        for trial in 0..200 {
            let n = 2 + next() % 9; // up to 10 nodes -> brute force is fast
            let mut edges = vec![];
            for u in 0..n {
                for v in (u + 1)..n {
                    if next() % 100 < 40 {
                        edges.push((u, v));
                    }
                }
            }
            let expected = brute_force_matching_size(n, &edges);
            assert_eq!(size_of(n, &edges), expected, "trial {trial}: n={n} edges={edges:?}");
        }
    }

    // exponential reference: try all subsets of edges
    fn brute_force_matching_size(n: usize, edges: &[(usize, usize)]) -> usize {
        fn go(edges: &[(usize, usize)], used: u64, n: usize) -> usize {
            if edges.is_empty() {
                return 0;
            }
            let (u, v) = edges[0];
            let rest = &edges[1..];
            let skip = go(rest, used, n);
            if used & (1 << u) == 0 && used & (1 << v) == 0 {
                skip.max(1 + go(rest, used | (1 << u) | (1 << v), n))
            } else {
                skip
            }
        }
        go(edges, 0, n)
    }
}
