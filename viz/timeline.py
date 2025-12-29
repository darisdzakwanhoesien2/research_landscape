import pandas as pd
import matplotlib.pyplot as plt

def plot_keyword_trend(df, keyword):
    trend = df[df["keywords"].apply(lambda x: keyword in x)]
    counts = trend.groupby("year").size()

    fig, ax = plt.subplots()
    counts.plot(ax=ax, marker="o")
    ax.set_title(f"Keyword Evolution: {keyword}")
    ax.set_ylabel("Publications")
    return fig