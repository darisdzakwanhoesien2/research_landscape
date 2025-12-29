import itertools
import networkx as nx
from collections import Counter

def build_cooccurrence_graph(df, min_freq=5):
    pairs = []

    for kws in df["keywords"]:
        pairs += list(itertools.combinations(set(kws), 2))

    freq = Counter(pairs)

    G = nx.Graph()
    for (a, b), w in freq.items():
        if w >= min_freq:
            G.add_edge(a, b, weight=w)

    return G