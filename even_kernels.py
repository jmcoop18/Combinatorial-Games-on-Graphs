from graphs import (
    build_graph,
    prism_graph_nodes, prism_graph_adjacency_listing,
    tri_grid_graph_nodes, tri_grid_graph_adjacency_listing,
    path_graph_nodes, path_graph_adjacency_listing,
    cycle_graph_nodes, cycle_graph_adjacency_listing,
    wheel_graph_nodes, wheel_graph_adjacency_listing,
    complete_split_graph_nodes, complete_split_graph_adjacency_listing,
)

import networkx as nx


def find_even_kernel(G, v, S, notS):
    
    neighbors = list(G.neighbors(v))
    [notS.append(n) for n in neighbors]
    
    for n in neighbors:
        adj = list(G.neighbors(n))
        kernel = sum(n in adj for n in S)
        
        if kernel % 2 == 1:
            S.append(adj[0])
    
    
    
    [find_even_kernel(G, node, S) for node in list(G.neighbors(v))]
    
   
   
   
   
    
n = 4
G = build_graph(tri_grid_graph_nodes(n), tri_grid_graph_adjacency_listing(n)) 
v = (0,0)
S = [v]
notS = []

find_even_kernel(G, v, S, notS)