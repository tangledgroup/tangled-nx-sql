import networkx as nx


def demo0():
    print('demo0')
    G = nx.DiGraph()
    G.add_edge('A', 'B', weight=0.1)
    G.add_edge('B', 'C', weight=0.1)
    G.add_edge('C', 'D', weight=0.1)
    G.add_edge('A', 'D', weight=0.3)

    path = nx.shortest_path(G, 'A', 'D', weight='weight')
    print(path)


def demo1():
    print('demo1')
    G = nx.DiGraph()
    G.add_edge('A', 'B', weight=0.1)
    G.add_edge('B', 'C', weight=0.1)
    G.add_edge('C', 'D', weight=0.1)
    G.add_edge('A', 'D', weight=0.4)

    path = nx.shortest_path(G, 'A', 'D', weight='weight')
    print(path)


if __name__ == '__main__':
    demo0()
    demo1()
