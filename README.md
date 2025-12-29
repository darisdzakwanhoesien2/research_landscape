1. Research References: https://scholar.google.com/scholar_labs/search/session/11716077684080802552?hl=en
2. ChatGPT: https://chatgpt.com/c/6951953b-0f9c-8333-b168-a9a2150f51f5

Below is a **complete, production-ready Streamlit app blueprint** (with runnable code) to **visualize the conference & journal paper landscape** using **knowledge maps + word cloud analysis**, directly grounded in the methodologies you listed (CiteSpace, VOSviewer, co-word analysis, bibliometrics, KG construction).

This is designed to fit **your current workflow** (you already work with Streamlit, large JSON/CSV pipelines, bibliometric data, and research intelligence dashboards).

---

# 🎓 Research Landscape Explorer (Streamlit App)

## 🎯 What this app does

It allows you to:

1. **Ingest academic metadata** (WoS / Scopus / OpenAlex / Semantic Scholar CSV/JSON)
2. **Clean & normalize keywords**
3. **Generate**

   * 📊 Word Clouds
   * 🧠 Keyword Co-occurrence Knowledge Graphs
   * ⏳ Temporal topic evolution
4. **Compare journals vs conferences**
5. **Export figures for papers (PNG / SVG)**

This mirrors workflows used in:

* Knowledge mapping papers (CiteSpace, UCINET, VOSviewer)
* Bibliometric + KG studies
* PRISMA-adjacent systematic landscape analysis (but exploratory)

---

## 📁 Project Structure

```
research_landscape_app/
│
├── app.py
├── requirements.txt
│
├── data/
│   ├── raw/
│   │   ├── papers.csv
│   │   └── papers.json
│   └── processed/
│
├── pipeline/
│   ├── loader.py
│   ├── cleaner.py
│   ├── keyword_extractor.py
│   ├── cooccurrence.py
│   └── temporal.py
│
├── viz/
│   ├── wordclouds.py
│   ├── network.py
│   └── timeline.py
│
└── utils/
    ├── text.py
    └── stopwords.py
```

---

## 📦 `requirements.txt`

```txt
streamlit
pandas
numpy
networkx
matplotlib
seaborn
wordcloud
scikit-learn
pyvis
python-louvain
```

---

## 📄 Input Data Format (CSV or JSON)

Minimum required fields:

```csv
title,abstract,keywords,year,source_type,venue
```

Where:

* `keywords`: `"cloud computing; healthcare; iot"`
* `source_type`: `journal | conference`
* `venue`: journal or conference name

---

## 🧠 Core Pipeline

---

### 🔹 `pipeline/loader.py`

```python

```

---

### 🔹 `pipeline/cleaner.py`

```python

```

---

### 🔹 `pipeline/cooccurrence.py`

```python

```

---

## 🎨 Visualizations

---

### 🔹 Word Cloud

`viz/wordclouds.py`

```python

```

---

### 🔹 Knowledge Graph (Interactive)

`viz/network.py`

```python

```

---

### 🔹 Temporal Evolution

`viz/timeline.py`

```python

```

---

## 🖥️ `app.py` (Main Streamlit App)

```python

```

---

## 🧪 What This Covers from Your Sources

| Method                      | Implemented             |
| --------------------------- | ----------------------- |
| Co-word analysis            | ✅                       |
| Knowledge maps              | ✅                       |
| Keyword clustering          | ✅ (via graph structure) |
| Word cloud                  | ✅                       |
| Journal + conference        | ✅                       |
| Temporal evolution          | ✅                       |
| PRISMA-adjacent exploratory | ✅                       |

This mirrors **CiteSpace / VOSviewer pipelines**, but:

* Fully open-source
* Customizable
* Reproducible
* Paper-ready

---

## 🚀 Next Extensions (Recommended)

Given your background, the **next logical upgrades** would be:

1. **Louvain clustering → research themes**
2. **Sankey topic evolution**
3. **Named Entity → Knowledge Graph**
4. **LLM-assisted keyword normalization**
5. **PRISMA diagram auto-generation**
6. **Export LaTeX-ready figures**

If you want, I can:

* Add **OpenAlex / Semantic Scholar API ingestion**
* Convert this into a **research-grade methods section**
* Add **citation burst detection (CiteSpace-like)**

Just tell me which direction you want next.
# research_landscape
