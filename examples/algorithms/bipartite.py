"""Demonstrate bipartite graph algorithms with nx_sql.

Tests bipartite property checking, projections, and bipartite centrality measures.
A bipartite graph has nodes partitionable into two sets with no intra-set edges.
"""

import networkx as nx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import nx_sql
from nx_sql.models import Base

engine = create_engine("sqlite:///nx_sql.db")
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)


def demo_bipartite():
    """Test bipartite graph algorithms on a projection of the Davis women's club data."""

    with Session() as session:
        # Create a bipartite graph
        G_nx = nx.davis_southern_women_graph()
        G = nx_sql.Graph(session, name="bipartite_demo")
        G.add_nodes_from(G_nx.nodes())
        G.add_edges_from(G_nx.edges())

        print(f"=== Bipartite Graph Analysis ===")
        print(f"Graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

        # Check if bipartite
        is_bip = nx.is_bipartite(G)
        print(f"Is bipartite: {is_bip}")

        if is_bip:
            # Get the two sets
            sets = nx.bipartite.sets(G)
            print(f"\nBipartite sets:")
            print(f"  Set 0 ({len(sets[0])} nodes): {sorted(sets[0])}")
            print(f"  Set 1 ({len(sets[1])} nodes): {sorted(sets[1])}")

            # Project onto one set (women's projection)
            women = sets[0]
            projected = nx.bipartite.projected_graph(G, women)
            print(f"\nWomen's projection: {projected.number_of_nodes()} nodes, {projected.number_of_edges()} edges")
            print(f"Top 5 women by connections in projection:")
            for node, deg in sorted(projected.degree(), key=lambda x: x[1], reverse=True)[:5]:
                print(f"  {node}: {deg} connections")

            # Weighted projection (shared events as weight)
            weighted = nx.bipartite.weighted_projected_graph(G, women)
            print(f"\nWeighted women's projection: {weighted.number_of_nodes()} nodes, {weighted.number_of_edges()} edges")

            # Density comparison
            full_density = nx.density(G)
            proj_density = nx.density(projected)
            print(f"\nDensity: full={full_density:.4f}, projected={proj_density:.4f}")

        session.commit()


if __name__ == "__main__":
    demo_bipartite()
