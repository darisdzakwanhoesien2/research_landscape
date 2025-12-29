from wordcloud import WordCloud
import matplotlib.pyplot as plt
from collections import Counter


def plot_wordcloud(df):
    """
    Safely plot a word cloud.
    Returns None if no words are available.
    """

    words = Counter()

    for kws in df["keywords"]:
        if isinstance(kws, list):
            words.update(kws)

    # 🔒 HARD GUARD (THIS PREVENTS YOUR ERROR)
    if len(words) == 0:
        return None

    wc = WordCloud(
        width=1200,
        height=600,
        background_color="white",
        collocations=False
    ).generate_from_frequencies(words)

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.imshow(wc)
    ax.axis("off")

    return fig


# from wordcloud import WordCloud
# import matplotlib.pyplot as plt
# from collections import Counter

# def plot_wordcloud(df):
#     words = Counter()
#     for kws in df["keywords"]:
#         words.update(kws)

#     wc = WordCloud(
#         width=1200,
#         height=600,
#         background_color="white"
#     ).generate_from_frequencies(words)

#     fig, ax = plt.subplots(figsize=(12, 6))
#     ax.imshow(wc)
#     ax.axis("off")
#     return fig