import re
import sys
import time

from graphs import (
    build_graph,
    prism_graph_nodes, prism_graph_adjacency_listing,
    tri_grid_graph_nodes, tri_grid_graph_adjacency_listing,
    path_graph_nodes, path_graph_adjacency_listing,
    cycle_graph_nodes, cycle_graph_adjacency_listing,
    wheel_graph_nodes, wheel_graph_adjacency_listing,
    complete_split_graph_nodes, complete_split_graph_adjacency_listing,
    rect_grid_graph_nodes, rect_grid_graph_adjacency_listing,
    complete_graph_nodes, complete_graph_adjacency_listing,
    complete_multipartite_graph_nodes, complete_multipartite_graph_adjacency_listing,
)
from nimber import find_nimber, nimber_output
from gf2_even_kernel import all_even_kernels, has_zero_or_two_neighbors


# ============================================================================
# CLI: top-level choice of algorithm (nimbers for AAC, or even kernels), then
# menu-driven graph selection shared by both
# ============================================================================

# single-size graph families: choice -> (nodes_fn, adjacency_fn, label)
GRAPH_TYPES = {
    1: (prism_graph_nodes, prism_graph_adjacency_listing, 'D'),
    2: (cycle_graph_nodes, cycle_graph_adjacency_listing, 'C'),
    3: (wheel_graph_nodes, wheel_graph_adjacency_listing, 'W'),
    4: (path_graph_nodes, path_graph_adjacency_listing, 'P'),
    5: (tri_grid_graph_nodes, tri_grid_graph_adjacency_listing, 'T'),
    7: (complete_graph_nodes, complete_graph_adjacency_listing, 'K'),
}


# prints the graph type menu; returns the chosen option as an int, or None on 'q'
def graph_type_menu():
    print(' ===== Graph Types ===== ')
    print('(1) - Prism Graph')
    print('(2) - Cycle Graph')
    print('(3) - Wheel Graph')
    print('(4) - Path Graph')
    print('(5) - Triangular Grid Graph')
    print('(6) - Rectangular Grid Graph')
    print('(7) - Complete Graph')
    print('(8) - Complete Split Graph')
    print('(9) - Complete Multipartite Graph K(m,...,m)')
    print('(10) - Custom Adjacency Listing')
    print('(q) - Back')
    choice = input('Enter the option you would like (1-10, \'q\' to go back): ').strip().lower()
    print()
    if choice == 'q':
        return None
    return int(choice)


# reads a custom graph from stdin as "i,j" edge pairs
def read_custom_graph():
    n = int(input('How many vertices are in your graph? '))
    print('Type or paste your adjacency listing as "i,j" pairs, separated by newlines.')
    print('When finished, press Enter then Ctrl+D (Ctrl+Z then Enter on Windows):')
    raw = sys.stdin.read()
    pairs = re.split(r'[;\s]+', raw.strip())
    listing = [tuple(int(x) for x in pair.split(',')) for pair in pairs if pair]
    return build_graph(n, listing)


# runs find_nimber on G from vertex v and prints the result
def run_single(G, v):
    print()
    start = time.time()
    nimber = nimber_output(find_nimber(G, v))
    print(f'Nimber from vertex {v} = {nimber}')
    print("Runtime:", time.time() - start, "seconds")


# runs find_nimber once per vertex, printing the nimber for each; vertices
# defaults to all of G, but symmetric families can pass representatives only
def iterate_all_vertices(G, vertices=None):
    print()
    for v in vertices if vertices is not None else G.nodes():
        start = time.time()
        nimber = nimber_output(find_nimber(G, v))
        print(f'v{v}: nimber {nimber}.  ({time.time() - start:.3f}s)')


# runs find_nimber from a fixed starting vertex v, once per size n in [n_start, n_end],
# building each graph via nodes_fn(n)/adjacency_fn(n); sizes where v isn't a vertex are skipped
def iterate_size_range(nodes_fn, adjacency_fn, label, n_start, n_end, v):
    print()
    for n in range(n_start, n_end + 1):
        G = build_graph(nodes_fn(n), adjacency_fn(n))
        if v not in G.nodes():
            print(f'{label}{n}: vertex {v} not in graph, skipping.')
            continue
        start = time.time()
        nimber = nimber_output(find_nimber(G, v))
        print(f'{label}{n}: nimber {nimber} from {v}.  ({time.time() - start:.3f}s)')


# runs find_nimber on complete split graphs CS(m, n) for every m in [m_start, m_end]
# and n in [n_start, n_end], starting from an inner (clique) vertex or an outer
# (independent set) vertex; inner vertices are all alike, so vertex 0 stands in
# for any of them, and likewise vertex m for the outer ones
def iterate_complete_split_grid(m_start, m_end, n_start, n_end, inner):
    print()
    kind = 'inner' if inner else 'outer'
    for m in range(m_start, m_end + 1):
        for n in range(n_start, n_end + 1):
            if (m == 0 and inner) or (n == 0 and not inner):
                print(f'K{m} + K{n}: no {kind} vertex, skipping.')
                continue
            G = build_graph(complete_split_graph_nodes(m, n), complete_split_graph_adjacency_listing(m, n))
            v = 0 if inner else m
            start = time.time()
            nimber = nimber_output(find_nimber(G, v))
            print(f'K{m} + K{n}: nimber {nimber} from {kind} vertex {v}.  ({time.time() - start:.3f}s)')
        print()


def nimber_menu():
    choice = graph_type_menu()
    if choice is None:
        return

    print(' ===== Run Type ===== ')
    print('(1) - Single run (fixed size, fixed starting vertex)')
    print('(2) - Iterate over all vertices (fixed size)')
    if choice not in [8, 10]:
        print('(3) - Iterate over a range of sizes (fixed starting vertex)')
    if choice == 8:
        print('(3) - Iterate over ranges of m and n (fixed inner/outer starting vertex)')
    mode = int(input('Enter the mode you would like: '))
    print()

    if choice in GRAPH_TYPES:
        nodes_fn, adjacency_fn, label = GRAPH_TYPES[choice]
    elif choice == 6:
        # rectangular grids take two sizes: fix the row count here, so the
        # single size parameter used below is the number of columns
        rows = int(input('Number of rows (m)? '))
        nodes_fn = lambda n: rect_grid_graph_nodes(rows, n)
        adjacency_fn = lambda n: rect_grid_graph_adjacency_listing(rows, n)
        label = f'R{rows}x'
    elif choice == 9:
        # multipartite graphs take two sizes: fix the number of parts here, so
        # the single size parameter used below is the part size m
        parts = int(input('How many parts (n)? '))
        nodes_fn = lambda m: complete_multipartite_graph_nodes(parts, m)
        adjacency_fn = lambda m: complete_multipartite_graph_adjacency_listing(parts, m)
        label = f'K{parts}x'
    elif choice == 8:
        if mode == 3:
            m_start = int(input('Starting complete graph size (m)? '))
            m_end = int(input('Ending complete graph size m (inclusive)? '))
            n_start = int(input('Starting independent node size n? '))
            n_end = int(input('Ending independent node size n (inclusive)? '))
            inner = input('Enter \'i\' to start from an inner vertex and \'o\' for an outer? ').strip().lower().startswith('i')
            iterate_complete_split_grid(m_start, m_end, n_start, n_end, inner)
            return
        # complete split graphs take two sizes: fix the complete graph size m here, so
        # the single size parameter used below is the independent set size n
        m = int(input('Size of the complete graph (m)? '))
        nodes_fn = lambda n: complete_split_graph_nodes(m, n)
        adjacency_fn = lambda n: complete_split_graph_adjacency_listing(m, n)
        label = f'K{m} + K'

    if choice in (1, 2, 3, 4, 5, 6, 7, 8, 9):
        # prism, tri grid, rect grid, and multipartite vertices are
        # (layer,index) pairs; the other families use int vertices
        def read_vertex(prompt):
            if choice in (1, 5, 6, 9):
                r, c = (int(i) for i in input(f'{prompt} (layer,index)? ').split(','))
                return (r, c)
            return int(input(f'{prompt}? '))

        if mode == 3:
            n_start = int(input(f'Starting size of {label} graph? '))
            n_end = int(input(f'Ending size of {label} graph (inclusive)? '))
            v = read_vertex('What is your fixed starting vertex')
            iterate_size_range(nodes_fn, adjacency_fn, label, n_start, n_end, v)
            return

        n = int(input(f'What size of graph? {label}'))
        G = build_graph(nodes_fn(n), adjacency_fn(n))

        if mode == 2:
            # in K(m,...,m) every vertex of a part is alike, so one per part suffices
            iterate_all_vertices(G, [(p, 0) for p in range(parts)] if choice == 9 else None)
            return

        v = read_vertex('What is your starting vertex')
        run_single(G, v)

    elif choice == 10:
        G = read_custom_graph()

        if mode == 2:
            iterate_all_vertices(G)
            return

        v = int(input('What is your starting vertex? '))
        run_single(G, v)


# reports how many nonempty even kernels G has (printing one), then whether
# any restricted (0 or 2 neighbors) even kernel contains vertex v
def even_kernel_single(G, v, name):
    print()
    start = time.time()
    kernels, _ = all_even_kernels(G)
    print(f'{name}: {len(kernels)} nonempty even kernel(s).')
    if kernels:
        print(kernels[0])

    restricted_with_v = [S for S in kernels
                         if v in S and has_zero_or_two_neighbors(G, S)]
    if restricted_with_v:
        print(f'{v} is in a restricted even kernel: {restricted_with_v[0]}')
    else:
        print(f'{v} is not in any restricted even kernels.')
    print(f'Runtime: {time.time() - start:.3f} seconds')


# for each vertex, reports whether some restricted even kernel contains it;
# the kernels are computed once since they don't depend on the vertex, and
# vertices defaults to all of G (symmetric families can pass representatives)
def even_kernel_all_vertices(G, vertices=None):
    print()
    start = time.time()
    kernels, _ = all_even_kernels(G)
    restricted = [S for S in kernels if has_zero_or_two_neighbors(G, S)]
    for v in vertices if vertices is not None else G.nodes():
        if any(v in S for S in restricted):
            print(f'v{v}: in a restricted even kernel.')
        else:
            print(f'v{v}: not in any restricted even kernels.')
    print(f'Runtime: {time.time() - start:.3f} seconds')


# for each size n in [n_start, n_end], reports how many nonempty even kernels
# the graph has and whether a restricted even kernel contains the fixed vertex v;
# sizes where v isn't a vertex are skipped
def even_kernel_size_range(nodes_fn, adjacency_fn, label, n_start, n_end, v):
    print()
    for n in range(n_start, n_end + 1):
        G = build_graph(nodes_fn(n), adjacency_fn(n))
        if v not in G.nodes():
            print(f'{label}{n}: vertex {v} not in graph, skipping.')
            continue
        start = time.time()
        kernels, _ = all_even_kernels(G)
        in_restricted = any(v in S and has_zero_or_two_neighbors(G, S) for S in kernels)
        status = (f'{v} is in a restricted even kernel' if in_restricted
                  else f'{v} is not in any restricted even kernels')
        print(f'{label}{n}: {len(kernels)} nonempty even kernel(s); {status}.  ({time.time() - start:.3f}s)')


# prompts for a graph, run type, and vertex, then runs the matching even
# kernel routine
def even_kernel_menu():
    choice = graph_type_menu()
    if choice is None:
        return

    print(' ===== Run Type ===== ')
    print('(1) - Single run (fixed size, fixed starting vertex)')
    print('(2) - Iterate over all vertices (fixed size)')
    if choice not in [8, 10]:
        print('(3) - Iterate over a range of sizes (fixed starting vertex)')
    mode = int(input('Enter the mode you would like: '))
    print()

    # prism, tri grid, rect grid, and multipartite vertices are (layer,index)
    # pairs; the rest are ints
    def read_vertex(prompt):
        if choice in (1, 5, 6, 9):
            r, c = (int(i) for i in input(f'{prompt} (layer,index)? ').split(','))
            return (r, c)
        return int(input(f'{prompt}? '))

    if choice in GRAPH_TYPES or choice in (6, 9):
        if choice in GRAPH_TYPES:
            nodes_fn, adjacency_fn, label = GRAPH_TYPES[choice]
        elif choice == 6:
            # rectangular grids take two sizes: fix the row count here, so the
            # single size parameter used below is the number of columns
            rows = int(input('Number of rows (m)? '))
            nodes_fn = lambda n: rect_grid_graph_nodes(rows, n)
            adjacency_fn = lambda n: rect_grid_graph_adjacency_listing(rows, n)
            label = f'R{rows}x'
        else:
            # multipartite graphs take two sizes: fix the number of parts here,
            # so the single size parameter used below is the part size m
            parts = int(input('How many parts (n)? '))
            nodes_fn = lambda m: complete_multipartite_graph_nodes(parts, m)
            adjacency_fn = lambda m: complete_multipartite_graph_adjacency_listing(parts, m)
            label = f'K{parts}x'

        if mode == 3:
            n_start = int(input(f'Starting size of {label} graph? '))
            n_end = int(input(f'Ending size of {label} graph (inclusive)? '))
            v = read_vertex('What is your fixed starting vertex')
            even_kernel_size_range(nodes_fn, adjacency_fn, label, n_start, n_end, v)
            return

        n = int(input(f'What size of graph? {label}'))
        G = build_graph(nodes_fn(n), adjacency_fn(n))
        name = f'{label}{n}'
    elif choice == 8:
        m = int(input('Size of the complete graph (m)? '))
        n = int(input('Size of the independent set (n)? '))
        G = build_graph(complete_split_graph_nodes(m, n), complete_split_graph_adjacency_listing(m, n))
        name = f'K{m} + K{n}'
    elif choice == 10:
        G = read_custom_graph()
        name = 'custom graph'
    else:
        print('Unknown graph type.')
        return

    if mode == 2:
        # in K(m,...,m) every vertex of a part is alike, so one per part suffices
        even_kernel_all_vertices(G, [(p, 0) for p in range(parts)] if choice == 9 else None)
        return

    v = read_vertex('What is your chosen vertex')
    if v not in G.nodes():
        print(f'Vertex {v} is not in {name}.')
        return
    even_kernel_single(G, v, name)


def menu():
    print(' ===== Algorithms ===== ')
    print('(1) - Nimbers for AAC')
    print('(2) - Even Kernels')
    print('(q) - Quit')
    choice = input('Enter the option you would like (1-2, \'q\' to quit): ').strip().lower()
    print()

    if choice == 'q':
        return False
    if choice == '1':
        nimber_menu()
    elif choice == '2':
        even_kernel_menu()
    else:
        print('Unknown option.')
    return True


if __name__ == '__main__':
    while menu():
        input('\nPress Enter to continue...')
        print()
