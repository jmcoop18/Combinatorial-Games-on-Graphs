// Python bindings. API mirrors X-Blossom's entry point:
//   x_blossom_maximum_matching(Graph& G, std::vector<int>& M, int num_threads)
// becomes
//   xblossom.maximum_matching(row_offsets, column_indices, num_threads=1) -> list[int]
// where the return value is M: M[v] = matched partner of v, or -1.

mod blossom;
mod graph;

use graph::Graph;
use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;

fn build_csr(row_offsets: Vec<usize>, column_indices: Vec<usize>) -> PyResult<Graph> {
    Graph::new(row_offsets, column_indices).map_err(PyValueError::new_err)
}

/// Maximum matching on a CSR graph. Returns M with M[v] = partner or -1.
/// `num_threads` is accepted for X-Blossom API parity; the kernel is
/// currently serial and ignores it.
#[pyfunction]
#[pyo3(signature = (row_offsets, column_indices, num_threads = 1))]
fn maximum_matching(
    py: Python<'_>,
    row_offsets: Vec<usize>,
    column_indices: Vec<usize>,
    num_threads: usize,
) -> PyResult<Vec<i64>> {
    let g = build_csr(row_offsets, column_indices)?;
    // release the GIL during the search so other Python threads can run
    py.allow_threads(move || Ok(blossom::maximum_matching(&g, num_threads)))
}

/// Size of a maximum matching on a CSR graph.
#[pyfunction]
#[pyo3(signature = (row_offsets, column_indices, num_threads = 1))]
fn matching_size(
    py: Python<'_>,
    row_offsets: Vec<usize>,
    column_indices: Vec<usize>,
    num_threads: usize,
) -> PyResult<usize> {
    let g = build_csr(row_offsets, column_indices)?;
    py.allow_threads(move || {
        let mate = blossom::maximum_matching(&g, num_threads);
        Ok(blossom::matching_size(&mate))
    })
}

/// Convenience form taking an edge list over nodes 0..num_nodes-1
/// (avoids building CSR on the Python side).
#[pyfunction]
fn matching_size_edges(
    py: Python<'_>,
    num_nodes: usize,
    edges: Vec<(usize, usize)>,
) -> PyResult<usize> {
    let g = Graph::from_edges(num_nodes, &edges).map_err(PyValueError::new_err)?;
    py.allow_threads(move || {
        let mate = blossom::maximum_matching(&g, 1);
        Ok(blossom::matching_size(&mate))
    })
}

/// Maximum matching from an edge list. Returns M with M[v] = partner or -1.
#[pyfunction]
fn maximum_matching_edges(
    py: Python<'_>,
    num_nodes: usize,
    edges: Vec<(usize, usize)>,
) -> PyResult<Vec<i64>> {
    let g = Graph::from_edges(num_nodes, &edges).map_err(PyValueError::new_err)?;
    py.allow_threads(move || Ok(blossom::maximum_matching(&g, 1)))
}

#[pymodule]
fn xblossom(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(maximum_matching, m)?)?;
    m.add_function(wrap_pyfunction!(matching_size, m)?)?;
    m.add_function(wrap_pyfunction!(maximum_matching_edges, m)?)?;
    m.add_function(wrap_pyfunction!(matching_size_edges, m)?)?;
    Ok(())
}
