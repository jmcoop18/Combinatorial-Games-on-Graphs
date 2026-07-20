import itertools
import os
import re
import select
import sys
import termios
import time
import tty

from graphs import (
    build_graph,
    prism_graph_nodes, prism_graph_adjacency_listing,
    tri_grid_graph_nodes, tri_grid_graph_adjacency_listing,
    path_graph_nodes, path_graph_adjacency_listing,
    cycle_graph_nodes, cycle_graph_adjacency_listing,
    wheel_graph_nodes, wheel_graph_adjacency_listing,
    generalized_wheel_graph_nodes, generalized_wheel_graph_adjacency_listing,
    complete_split_graph_nodes, complete_split_graph_adjacency_listing,
    rect_grid_graph_nodes, rect_grid_graph_adjacency_listing,
    complete_graph_nodes, complete_graph_adjacency_listing,
    complete_multipartite_graph_nodes, complete_multipartite_graph_adjacency_listing,
)
from nimber import nimber_output, multipartite_AAC_nimber, blossomX_AAC_nimber
from gf2_even_kernel import all_even_kernels, has_zero_or_two_neighbors


# ============================================================================
# CLI: top-level choice of algorithm (nimbers for AAC, or even kernels), then
# menu-driven graph selection shared by both
# ============================================================================

# every answer typed during a run is recorded so the main menu's 'r' option
# can replay the whole selection; _replay_queue holds the answers being
# replayed (None when reading from the keyboard as usual)
_last_run = []
_current_run = []
_replay_queue = None


# input() replacement that reads the keyboard one keypress at a time so a
# lone Esc press exits the program immediately, from any prompt; falls back
# to plain input() when stdin isn't a terminal (e.g. piped input)
def read_line(prompt=''):
    if not sys.stdin.isatty():
        return input(prompt)
    print(prompt, end='', flush=True)
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    # bytes are read straight from the fd (not sys.stdin, which buffers
    # ahead and would make the lone-Esc check below misfire on arrow keys)
    buf = bytearray()
    try:
        tty.setcbreak(fd)  # keypress-at-a-time, but Ctrl+C still works
        while True:
            ch = os.read(fd, 1)
            if ch == b'\x1b':  # Esc
                # arrow keys etc. arrive as Esc followed by more bytes;
                # only a lone Esc means the user wants to exit
                if not select.select([fd], [], [], 0.05)[0]:
                    print('\n\nGoodbye!')
                    sys.exit(0)
                # swallow the rest of the escape sequence and ignore it
                while select.select([fd], [], [], 0.01)[0]:
                    os.read(fd, 1)
            elif ch in (b'\n', b'\r'):
                print()
                return buf.decode()
            elif ch in (b'\x7f', b'\x08'):  # backspace
                if buf:
                    buf.pop()
                    print('\b \b', end='', flush=True)
            elif ch == b'\x04':  # Ctrl+D
                raise EOFError
            else:
                buf += ch
                sys.stdout.buffer.write(ch)
                sys.stdout.flush()
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


# input() replacement: records the answer, and during a replay silently
# consumes the saved answer instead of prompting
def ask(prompt):
    global _replay_queue
    if _replay_queue:
        answer = _replay_queue.pop(0)
    else:
        answer = read_line(prompt)
    _current_run.append(answer)
    return answer


# sys.stdin.read() replacement (custom adjacency listings), recorded the same way
def ask_multiline():
    global _replay_queue
    if _replay_queue:
        raw = _replay_queue.pop(0)
    else:
        raw = sys.stdin.read()
    _current_run.append(raw)
    return raw

# single-size graph families: choice -> (nodes_fn, adjacency_fn, label)
GRAPH_TYPES = {
    1: (prism_graph_nodes, prism_graph_adjacency_listing, 'D'),
    2: (path_graph_nodes, path_graph_adjacency_listing, 'P'),
    3: (cycle_graph_nodes, cycle_graph_adjacency_listing, 'C'),
    4: (wheel_graph_nodes, wheel_graph_adjacency_listing, 'W'),
    6: (tri_grid_graph_nodes, tri_grid_graph_adjacency_listing, 'T'),
    8: (complete_graph_nodes, complete_graph_adjacency_listing, 'K'),
}


# prints the graph type menu (skipped during a rerun); returns the chosen
# option as an int, or None on 'q'
def graph_type_menu():
    if not _replay_queue:
        print(' ===== Graph Types ===== ')
        print('(1) - Prism Graph')
        print('(2) - Path Graph')
        print('(3) - Cycle Graph')
        print('(4) - Wheel Graph')
        print('(5) - Generalized Wheel Graph')
        print('(6) - Triangular Grid Graph')
        print('(7) - Rectangular Grid Graph')
        print('(8) - Complete Graph')
        print('(9) - Complete Split Graph')
        print('(10) - Complete K-partite Graph')
        print('(11) - Custom Adjacency Listing')
        print('(b) - Back')
    choice = ask('Enter the option you would like (1-11, \'b\' to go back): ').strip().lower()
    if not _replay_queue:
        print()
    if choice == 'b':
        return None
    return int(choice)


# reads a custom graph from stdin as "i,j" edge pairs
def read_custom_graph():
    n = int(ask('How many vertices are in your graph? '))
    print('Type or paste your adjacency listing as "i,j" pairs, separated by newlines.')
    print('When finished, press Enter then Ctrl+D (Ctrl+Z then Enter on Windows):')
    raw = ask_multiline()
    pairs = re.split(r'[;\s]+', raw.strip())
    listing = [tuple(int(x) for x in pair.split(',')) for pair in pairs if pair]
    return build_graph(n, listing)


# runs blossomX_AAC_nimber on G from vertex v and prints the result
def run_single(G, v):
    print()
    start = time.time()
    nimber = nimber_output(blossomX_AAC_nimber(G, v))
    print(f'Nimber from vertex {v} = {nimber}')
    print("Runtime:", time.time() - start, "seconds")


# runs the closed-form multipartite solver on K(sizes) from a vertex in part p
def run_single_multipartite(sizes, p):
    print()
    start = time.time()
    nimber = nimber_output(multipartite_AAC_nimber(sizes, p))
    print(f'Nimber from part {p} = {nimber}')
    print("Runtime:", time.time() - start, "seconds")


# runs the closed-form multipartite solver once per part of K(sizes);
# vertices of a part are all alike, so one representative per part suffices
def iterate_all_parts(sizes):
    print()
    for p in range(len(sizes)):
        start = time.time()
        nimber = nimber_output(multipartite_AAC_nimber(sizes, p))
        print(f'part {p} (size {sizes[p]}): nimber {nimber}.  ({time.time() - start:.3f}s)')


# runs blossomX_AAC_nimber once per vertex, printing the nimber for each; vertices
# defaults to all of G, but symmetric families can pass representatives only
def iterate_all_vertices(G, vertices=None):
    print()
    for v in vertices if vertices is not None else G.nodes():
        start = time.time()
        nimber = nimber_output(blossomX_AAC_nimber(G, v))
        print(f'v{v}: nimber {nimber}.  ({time.time() - start:.3f}s)')


# runs blossomX_AAC_nimber from a fixed starting vertex v, once per size n in [n_start, n_end],
# building each graph via nodes_fn(n)/adjacency_fn(n); sizes where v isn't a vertex are skipped
def iterate_size_range(nodes_fn, adjacency_fn, label, n_start, n_end, v):
    print()
    for n in range(n_start, n_end + 1):
        G = build_graph(nodes_fn(n), adjacency_fn(n))
        if v not in G.nodes():
            print(f'{label}{n}: vertex {v} not in graph, skipping.')
            continue
        start = time.time()
        nimber = nimber_output(blossomX_AAC_nimber(G, v))
        print(f'{label}{n}: nimber {nimber} from {v}.  ({time.time() - start:.3f}s)')


# runs blossomX_AAC_nimber on complete split graphs CS(m, n) for every m in [m_start, m_end]
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
            nimber = nimber_output(blossomX_AAC_nimber(G, v))
            print(f'K{m} + K{n}: nimber {nimber} from {kind} vertex {v}.  ({time.time() - start:.3f}s)')
        print()


# runs blossomX_AAC_nimber on generalized wheel graphs Cm + Kn for every m in
# [m_start, m_end] and n in [n_start, n_end], starting from a cycle vertex or
# a split (clique) vertex; cycle vertices are all alike, so vertex 0 stands in
# for any of them, and likewise vertex m for the split vertices
def iterate_generalized_wheel_grid(m_start, m_end, n_start, n_end, inner):
    print()
    kind = 'split' if inner else 'cycle'
    for m in range(m_start, m_end + 1):
        for n in range(n_start, n_end + 1):
            if (n == 0 and inner) or (m == 0 and not inner):
                print(f'C{m} + K{n}: no {kind} vertex, skipping.')
                continue
            G = build_graph(generalized_wheel_graph_nodes(m, n), generalized_wheel_graph_adjacency_listing(m, n))
            v = m if inner else 0
            start = time.time()
            nimber = nimber_output(blossomX_AAC_nimber(G, v))
            print(f'C{m} + K{n}: nimber {nimber} from {kind} vertex {v}.  ({time.time() - start:.3f}s)')
        print()


def nimber_menu():
    choice = graph_type_menu()
    if choice is None:
        return

    if not _replay_queue:
        print(' ===== Run Type ===== ')
        print('(1) - Single run (fixed size, fixed starting vertex)')
        print('(2) - Iterate over all vertices (fixed size)')
        if choice not in [5, 9, 10, 11]:
            print('(3) - Iterate over a range of sizes (fixed starting vertex)')
        if choice in (5, 9):
            print('(3) - Iterate over ranges of m and n (fixed inner/outer starting vertex)')
    mode = int(ask('Enter the mode you would like: '))
    print()

    if choice in GRAPH_TYPES:
        nodes_fn, adjacency_fn, label = GRAPH_TYPES[choice]
    elif choice == 7:
        # rectangular grids take two sizes: fix the row count here, so the
        # single size parameter used below is the number of columns
        rows = int(ask('Number of rows (m)? '))
        nodes_fn = lambda n: rect_grid_graph_nodes(rows, n)
        adjacency_fn = lambda n: rect_grid_graph_adjacency_listing(rows, n)
        label = f'R{rows}x'
    elif choice == 10:
        # parts may have different sizes, entered as a comma-separated list
        sizes = [int(t) for t in ask('Part sizes (comma-separated, e.g. 2,3,5)? ').split(',')]
    elif choice == 5:
        if mode == 3:
            m_start = int(ask('Starting cycle size (m)? '))
            m_end = int(ask('Ending cycle size m (inclusive)? '))
            n_start = int(ask('Starting complete graph size n? '))
            n_end = int(ask('Ending complete graph size n (inclusive)? '))
            inner = ask('Enter \'s\' to start from a split vertex and \'c\' for a cycle vertex? ').strip().lower().startswith('s')
            iterate_generalized_wheel_grid(m_start, m_end, n_start, n_end, inner)
            return
        # generalized wheel graphs take two sizes: fix the cycle size m here, so
        # the single size parameter used below is the complete graph size n
        m = int(ask('Size of the cycle (m)? '))
        nodes_fn = lambda n: generalized_wheel_graph_nodes(m, n)
        adjacency_fn = lambda n: generalized_wheel_graph_adjacency_listing(m, n)
        label = f'C{m} + K'
    elif choice == 9:
        if mode == 3:
            m_start = int(ask('Starting complete graph size (m)? '))
            m_end = int(ask('Ending complete graph size m (inclusive)? '))
            n_start = int(ask('Starting independent node size n? '))
            n_end = int(ask('Ending independent node size n (inclusive)? '))
            inner = ask('Enter \'i\' to start from an inner vertex and \'o\' for an outer? ').strip().lower().startswith('i')
            iterate_complete_split_grid(m_start, m_end, n_start, n_end, inner)
            return
        # complete split graphs take two sizes: fix the complete graph size m here, so
        # the single size parameter used below is the independent set size n
        m = int(ask('Size of the complete graph (m)? '))
        nodes_fn = lambda n: complete_split_graph_nodes(m, n)
        adjacency_fn = lambda n: complete_split_graph_adjacency_listing(m, n)
        label = f'K{m} + K'

    if choice == 10:
        # the closed-form solver works on the part sizes directly, so no
        # graph is ever built for complete multipartite nimbers
        if mode == 2:
            iterate_all_parts(sizes)
            return
        p = int(ask('What is your starting vertex (part number)? '))
        run_single_multipartite(sizes, p)

    elif choice in (1, 2, 3, 4, 5, 6, 7, 8, 9):
        # prism, tri grid, and rect grid vertices are (layer,index) pairs;
        # the other families use int vertices
        def read_vertex(prompt):
            if choice in (1, 6, 7):
                r, c = (int(i) for i in ask(f'{prompt} (layer,index)? ').split(','))
                return (r, c)
            return int(ask(f'{prompt}? '))

        if mode == 3:
            n_start = int(ask(f'Starting size of {label} graph? '))
            n_end = int(ask(f'Ending size of {label} graph (inclusive)? '))
            v = read_vertex('What is your fixed starting vertex')
            iterate_size_range(nodes_fn, adjacency_fn, label, n_start, n_end, v)
            return

        n = int(ask(f'What size of graph? {label}'))
        G = build_graph(nodes_fn(n), adjacency_fn(n))

        if mode == 2:
            iterate_all_vertices(G)
            return

        v = read_vertex('What is your starting vertex')
        run_single(G, v)

    elif choice == 11:
        G = read_custom_graph()

        if mode == 2:
            iterate_all_vertices(G)
            return

        v = int(ask('What is your starting vertex? '))
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

    if not _replay_queue:
        print(' ===== Run Type ===== ')
        print('(1) - Single run (fixed size, fixed starting vertex)')
        print('(2) - Iterate over all vertices (fixed size)')
        if choice not in [5, 9, 10, 11]:
            print('(3) - Iterate over a range of sizes (fixed starting vertex)')
    mode = int(ask('Enter the mode you would like: '))
    print()

    # prism, tri grid, and rect grid vertices are (layer,index) pairs;
    # multipartite vertices of a part are all alike, so only the part number
    # is asked for; the rest are ints
    def read_vertex(prompt):
        if choice == 10:
            return (int(ask(f'{prompt} (part number)? ')), 0)
        if choice in (1, 6, 7):
            r, c = (int(i) for i in ask(f'{prompt} (layer,index)? ').split(','))
            return (r, c)
        return int(ask(f'{prompt}? '))

    if choice in GRAPH_TYPES or choice in (7, 10):
        if choice in GRAPH_TYPES:
            nodes_fn, adjacency_fn, label = GRAPH_TYPES[choice]
        elif choice == 7:
            # rectangular grids take two sizes: fix the row count here, so the
            # single size parameter used below is the number of columns
            rows = int(ask('Number of rows (m)? '))
            nodes_fn = lambda n: rect_grid_graph_nodes(rows, n)
            adjacency_fn = lambda n: rect_grid_graph_adjacency_listing(rows, n)
            label = f'R{rows}x'
        else:
            # parts may have different sizes, entered as a comma-separated list
            sizes = [int(t) for t in ask('Part sizes (comma-separated, e.g. 2,3,5)? ').split(',')]

        if mode == 3:
            n_start = int(ask(f'Starting size of {label} graph? '))
            n_end = int(ask(f'Ending size of {label} graph (inclusive)? '))
            v = read_vertex('What is your fixed starting vertex')
            even_kernel_size_range(nodes_fn, adjacency_fn, label, n_start, n_end, v)
            return

        if choice == 10:
            G = build_graph(complete_multipartite_graph_nodes(sizes),
                            complete_multipartite_graph_adjacency_listing(sizes))
            name = f'K({",".join(str(s) for s in sizes)})'
        else:
            n = int(ask(f'What size of graph? {label}'))
            G = build_graph(nodes_fn(n), adjacency_fn(n))
            name = f'{label}{n}'
    elif choice == 5:
        m = int(ask('Size of the cycle (m)? '))
        n = int(ask('Size of the complete graph (n)? '))
        G = build_graph(generalized_wheel_graph_nodes(m, n), generalized_wheel_graph_adjacency_listing(m, n))
        name = f'C{m} + K{n}'
    elif choice == 9:
        m = int(ask('Size of the complete graph (m)? '))
        n = int(ask('Size of the independent set (n)? '))
        G = build_graph(complete_split_graph_nodes(m, n), complete_split_graph_adjacency_listing(m, n))
        name = f'K{m} + K{n}'
    elif choice == 11:
        G = read_custom_graph()
        name = 'custom graph'
    else:
        print('Unknown graph type.')
        return

    if mode == 2:
        # in a complete multipartite graph every vertex of a part is alike,
        # so one representative per part suffices
        even_kernel_all_vertices(G, [(p, 0) for p in range(len(sizes))] if choice == 10 else None)
        return

    v = read_vertex('What is your chosen vertex')
    if v not in G.nodes():
        print(f'Vertex {v} is not in {name}.')
        return
    even_kernel_single(G, v, name)


# runs the chosen algorithm, then saves the recorded answers for replay
def run_choice(choice):
    global _last_run, _replay_queue
    if choice == '1':
        nimber_menu()
    elif choice == '2':
        even_kernel_menu()
    else:
        print('Unknown option.')
        return
    # a bare 'q' means the run was backed out of at the graph type menu;
    # keep the previous completed selection in that case
    if 'q' not in _current_run:
        _last_run = _current_run
    _replay_queue = None


# replays the algorithm, graph type, and run type of the last completed
# selection (its first three recorded answers), then picks the menu back up
# there, prompting for sizes and vertices as usual
def rerun_last():
    global _current_run, _replay_queue
    _replay_queue = list(_last_run[:3])
    _current_run = [_replay_queue.pop(0)]
    run_choice(_current_run[0])


def menu():
    global _current_run, _replay_queue
    print(' ===== Algorithms ===== ')
    print('(Press Esc at any time to exit)')
    print('(1) - Nimbers for AAC')
    print('(2) - Even Kernels')
    choice = read_line('Enter the option you would like (1-2): ').strip().lower()
    print()

    _current_run = [choice]
    _replay_queue = None
    run_choice(choice)
    return True


# testing sweep: k-partite K(a1,...,a_{k-1},d) over all nondecreasing small
# part sizes a1 <= ... <= a_{k-1} <= c_max with dominant part
# d = a1 + ... + a_{k-1} + 1, printing the nimber from every part of each graph;
# run with `python cli.py sweep <k>` (k defaults to 4; plain `python cli.py`
# still opens the menu)
def sweep_kpartite(k=4, c_max=10):
    # compute every row first so the columns can be sized to the widest entries
    rows = []
    for small in itertools.combinations_with_replacement(range(1, c_max + 1), k - 1):
        d = sum(small) + 1
        sizes = list(small) + [d]
        label = f'K({",".join(str(s) for s in sizes)}):'
        nimbers = [str(nimber_output(multipartite_AAC_nimber(sizes, p))) for p in range(k)]
        rows.append((label, nimbers))
    label_width = max(len(label) for label, _ in rows)
    nimber_width = max(len(n) for _, nimbers in rows for n in nimbers)
    for label, nimbers in rows:
        print((label.ljust(label_width + 2) + '  '.join(n.ljust(nimber_width) for n in nimbers)).rstrip())


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] in ('sweep', 'sweep4'):
        k = int(sys.argv[2]) if len(sys.argv) > 2 else 4
        sweep_kpartite(k)
        sys.exit(0)
    keep_going = menu()
    while keep_going:
        hint = ' (or space + Enter to rerun the last graph & run type)' if _last_run else ''
        again = read_line(f'\nPress Enter to continue{hint}...')
        print()
        # a line of only whitespace (space then Enter) means rerun;
        # a bare Enter or anything else goes back to the menu
        if again and not again.strip() and _last_run:
            rerun_last()
        else:
            keep_going = menu()
