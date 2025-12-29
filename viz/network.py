from pyvis.network import Network

def build_interactive_graph(G):
    net = Network(height="700px", bgcolor="#ffffff", font_color="black")
    net.from_nx(G)
    net.repulsion(node_distance=200)
    return net