// CSR (Compressed Sparse Row) graph, matching X-Blossom's input format:
//   row_offsets:    length n+1; neighbors of v live at
//                   column_indices[row_offsets[v] .. row_offsets[v+1]]
//   column_indices: flattened neighbor lists
//
// Example: square 0-1-2-3-0 with diagonal 1-3:
//   row_offsets    = [0, 2, 5, 7, 10]
//   column_indices = [1, 3, 0, 2, 3, 1, 3, 0, 1, 2]

pub struct Graph {
    pub row_offsets: Vec<usize>,
    pub column_indices: Vec<usize>,
}

impl Graph {
    pub fn new(row_offsets: Vec<usize>, column_indices: Vec<usize>) -> Result<Self, String> {
        if row_offsets.is_empty() {
            return Err("row_offsets must have length n+1 (at least 1)".into());
        }
        let n = row_offsets.len() - 1;
        if *row_offsets.last().unwrap() != column_indices.len() {
            return Err(format!(
                "row_offsets ends at {} but column_indices has length {}",
                row_offsets.last().unwrap(),
                column_indices.len()
            ));
        }
        if row_offsets.windows(2).any(|w| w[0] > w[1]) {
            return Err("row_offsets must be non-decreasing".into());
        }
        if let Some(&bad) = column_indices.iter().find(|&&u| u >= n) {
            return Err(format!("neighbor index {bad} out of range for {n} nodes"));
        }
        Ok(Graph { row_offsets, column_indices })
    }

    // Build from an edge list; nodes must be 0..n-1. Duplicate edges and
    // self-loops are tolerated (self-loops never appear in a matching).
    pub fn from_edges(num_nodes: usize, edges: &[(usize, usize)]) -> Result<Self, String> {
        let mut degree = vec![0usize; num_nodes];
        for &(u, v) in edges {
            if u >= num_nodes || v >= num_nodes {
                return Err(format!("edge ({u}, {v}) out of range for {num_nodes} nodes"));
            }
            if u == v {
                continue;
            }
            degree[u] += 1;
            degree[v] += 1;
        }
        let mut row_offsets = vec![0usize; num_nodes + 1];
        for v in 0..num_nodes {
            row_offsets[v + 1] = row_offsets[v] + degree[v];
        }
        let mut column_indices = vec![0usize; row_offsets[num_nodes]];
        let mut cursor = row_offsets.clone();
        for &(u, v) in edges {
            if u == v {
                continue;
            }
            column_indices[cursor[u]] = v;
            cursor[u] += 1;
            column_indices[cursor[v]] = u;
            cursor[v] += 1;
        }
        Ok(Graph { row_offsets, column_indices })
    }

    #[inline]
    pub fn num_nodes(&self) -> usize {
        self.row_offsets.len() - 1
    }

    #[inline]
    pub fn neighbors(&self, v: usize) -> &[usize] {
        &self.column_indices[self.row_offsets[v]..self.row_offsets[v + 1]]
    }
}
