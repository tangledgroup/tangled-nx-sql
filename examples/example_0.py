import networkx as nx

eps = 1e-17

G = nx.DiGraph()
G.add_edge('A', 'B', weight=0.1)
G.add_edge('B', 'C', weight=0.1)
G.add_edge('C', 'D', weight=0.1)
G.add_edge('A', 'D', weight=0.3 + eps)

path = nx.shortest_path(G, 'A', 'D', weight='weight')
print(path)
