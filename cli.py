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
)
from nimber import find_nimber, nimber_output


# ============================================================================
# CLI: menu-driven runs against a single vertex, all vertices of one graph,
# or a range of graph sizes at a fixed vertex
# ============================================================================

# runs find_nimber on G from vertex v and prints the result
def run_single(G, v):
    print()
    start = time.time()
    nimber = nimber_output(find_nimber(G, v))
    print(f'Nimber from vertex {v} = {nimber}')
    print("Runtime:", time.time() - start, "seconds")


# runs find_nimber on G once per vertex of G, printing the nimber for each
def iterate_all_vertices(G):
    print()
    for v in G.nodes():
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


def menu():
    print(' ===== Graph Types ===== ')
    print('(1) - Prism Graph')
    print('(2) - Triangular Grid Graph')
    print('(3) - Path Graph')
    print('(4) - Cycle Graph')
    print('(5) - Wheel Graph')
    print('(6) - Complete Split Graph')
    print('(7) - Custom Adjacency Listing')
    print('(q) - Quit')
    choice = input('Enter the option you would like (1-7, \'q\' to quit): ').strip().lower()
    print()

    if choice == 'q':
        return False

    choice = int(choice)

    print(' ===== Run Type ===== ')
    print('(1) - Single run (fixed size, fixed starting vertex)')
    print('(2) - Iterate over all vertices (fixed size)')
    if choice not in [6, 7]:
        print('(3) - Iterate over a range of sizes (fixed starting vertex)')
    if choice == 6:
        print('(3) - Iterate over ranges of m and n (fixed inner/outer starting vertex)')
    mode = int(input('Enter the mode you would like: '))
    print()

    if choice == 1:
        nodes_fn, adjacency_fn, label = (
            prism_graph_nodes, prism_graph_adjacency_listing, 'D')
    elif choice == 2:
        nodes_fn, adjacency_fn, label = (
            tri_grid_graph_nodes, tri_grid_graph_adjacency_listing, 'T')
    elif choice == 3:
        nodes_fn, adjacency_fn, label = (
            path_graph_nodes, path_graph_adjacency_listing, 'P')
    elif choice == 4:
        nodes_fn, adjacency_fn, label = (
            cycle_graph_nodes, cycle_graph_adjacency_listing, 'C')
    elif choice == 5:
        nodes_fn, adjacency_fn, label = (
            wheel_graph_nodes, wheel_graph_adjacency_listing, 'W')
    elif choice == 6:
        if mode == 3:
            m_start = int(input('Starting complete graph size (m)? '))
            m_end = int(input('Ending complete graph size m (inclusive)? '))
            n_start = int(input('Starting independent node size n? '))
            n_end = int(input('Ending independent node size n (inclusive)? '))
            inner = input('Enter \'i\' to start from an inner vertex and \'o\' for an outer? ').strip().lower().startswith('i')
            iterate_complete_split_grid(m_start, m_end, n_start, n_end, inner)
            return True
        # complete split graphs take two sizes: fix the complete graph size m here, so
        # the single size parameter used below is the independent set size n
        m = int(input('Size of the complete graph (m)? '))
        nodes_fn = lambda n: complete_split_graph_nodes(m, n)
        adjacency_fn = lambda n: complete_split_graph_adjacency_listing(m, n)
        label = f'K{m} + K'

    if choice in (1, 2, 3, 4, 5, 6):
        # prism and tri grid vertices are (layer,index) pairs; path/cycle/wheel/complete split vertices are ints
        def read_vertex(prompt):
            if choice in (1, 2):
                r, c = (int(i) for i in input(f'{prompt} (layer,index)? ').split(','))
                return (r, c)
            return int(input(f'{prompt}? '))

        if mode == 3:
            n_start = int(input(f'Starting size of {label} graph? '))
            n_end = int(input(f'Ending size of {label} graph (inclusive)? '))
            v = read_vertex('What is your fixed starting vertex')
            iterate_size_range(nodes_fn, adjacency_fn, label, n_start, n_end, v)
            return True

        n = int(input(f'What size of graph? {label}'))
        G = build_graph(nodes_fn(n), adjacency_fn(n))

        if mode == 2:
            iterate_all_vertices(G)
            return True

        v = read_vertex('What is your starting vertex')
        run_single(G, v)

    elif choice == 7:
        n = int(input('How many vertices are in your graph? '))
        print('Type or paste your adjacency listing as "i,j" pairs, separated by newlines.')
        print('When finished, press Enter then Ctrl+D (Ctrl+Z then Enter on Windows):')
        raw = sys.stdin.read()
        pairs = re.split(r'[;\s]+', raw.strip())
        listing = [tuple(int(x) for x in pair.split(',')) for pair in pairs if pair]
        G = build_graph(n, listing)

        if mode == 2:
            iterate_all_vertices(G)
            return True

        v = int(input('What is your starting vertex? '))
        run_single(G, v)

    return True


if __name__ == '__main__':
    while menu():
        input('\nPress Enter to continue...')
        print()
