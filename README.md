1. https://chatgpt.com/c/695bbb2f-5644-8327-9c13-76501da9e35b

Yes — this is actually a **very strong use case for a Sankey diagram**, because your material naturally forms a **flow of ideas** rather than a flat table.

Below I’ll do **three things**, in order:

1. **Define the Sankey structure** (what connects to what)
2. **Explain *why* each connection exists** (the intellectual logic)
3. **Give you ready-to-use Sankey code (Plotly / Streamlit-friendly)** so you can visualize it immediately

---

## 1️⃣ Conceptual Sankey Structure

A clean Sankey for your project should have **three layers**:

```
[Research Themes]
        ↓
[Research Questions (RQs)]
        ↓
[Research Projects / Papers]
```

This mirrors how:

* **Themes** motivate inquiry
* **RQs operationalize themes**
* **Projects implement RQs**

### Layer 1 — Themes (Sources)

* Detecting Greenwashing and Deceptive Rhetoric
* Transparency and Rating Consistency
* Technological Innovations in ESG-NLP
* Financial Predictability and Risk Mitigation

### Layer 2 — Research Questions (Middle)

Condensed (important for Sankey clarity):

* Multimodal greenwashing detection
* Carbonwashing index
* Linguistic & tone disambiguity
* Rating inconsistency reconciliation
* Explainable ESG via KG / neurosymbolic AI
* SME ESG feasibility
* Real-time ESG intelligence
* ESG sentiment & financial risk

### Layer 3 — Research Projects (Targets)

* **Paper 1:** Carbonwashing via Multimodal Triangulation
* **Paper 2:** Neurosymbolic Scoring for Aggregate Confusion
* **Paper 3:** Predictive SME Credit Risk (Causal ESG)
* **Paper 4:** Real-Time ESG Intelligence (KG-RAG)

---

## 2️⃣ Why These Connections Make Sense (Critical Explanation)

This is the *most important* part — this is what supervisors, reviewers, and thesis committees care about.

---

### 🔹 Theme: Detecting Greenwashing & Deceptive Rhetoric

**Flows into:**

* Multimodal greenwashing detection
* Carbonwashing index
* Linguistic markers & tone disambiguity

**Why → Paper 1 (Carbonwashing via Multimodal Triangulation)**

> Greenwashing is *not purely linguistic*. Firms often use **strong sustainability language while emissions worsen**.

✔ Paper 1 directly addresses:

* **Discourse–practice gap**
* **Tone vs. physical reality**
* **Text + external data triangulation**

➡ Sankey logic:
**Theme → RQs → Paper 1** is *methodologically inevitable*.

---

### 🔹 Theme: Transparency & Rating Consistency

**Flows into:**

* Rating discrepancy across agencies
* Automated vs human scoring
* Readability & transparency effects

**Why → Paper 2 (Neurosymbolic Scoring)**

> ESG ratings fail not because of lack of data, but because **aggregation rules are opaque and inconsistent**.

✔ Paper 2 solves:

* Black-box criticism
* Regulatory alignment (CSRD, EU taxonomy)
* Explainability for auditors & regulators

➡ Sankey logic:
This is the **only paper that structurally resolves rating inconsistency**, so the flow is *exclusive and strong*.

---

### 🔹 Theme: Technological Innovations in ESG-NLP

**Flows into:**

* Domain-specific models (ClimateBERT, ESG-BERT)
* Knowledge graphs
* Neurosymbolic AI
* KG-RAG
* SME constraints

**Why → Paper 2, 3, and 4**

This theme **fans out**, because it is infrastructural.

* **Paper 2:** XAI via neurosymbolic reasoning
* **Paper 3:** Method transfer from large firms → SMEs
* **Paper 4:** Real-time KG-RAG monitoring

➡ Sankey logic:
This theme is a **methodological backbone**, not a single outcome.

---

### 🔹 Theme: Financial Predictability & Risk Mitigation

**Flows into:**

* ESG → credit risk
* ESG sentiment → market signals

**Why → Paper 3 (SME Credit Risk) & Paper 4 (KG-RAG)**

> Financial risk relevance emerges **only when ESG is timely and causal**, not descriptive.

* **Paper 3:** ESG as *causal driver* of SME creditworthiness
* **Paper 4:** ESG as *real-time risk signal* (litigation, governance shocks)

➡ Sankey logic:
Finance is not the goal — it is the **validation domain**.

---

## 3️⃣ Ready-to-Use Sankey Code (Plotly)

This works directly in **Jupyter, Streamlit, or Dash**.

```python
import plotly.graph_objects as go

labels = [
    # Themes
    "Greenwashing & Deceptive Rhetoric",
    "Transparency & Rating Consistency",
    "Technological Innovations in ESG-NLP",
    "Financial Predictability & Risk",

    # Research Questions
    "Multimodal Greenwashing Detection",
    "Carbonwashing Index",
    "Tone & Linguistic Disambiguity",
    "Rating Inconsistency",
    "Explainable ESG (KG / Neurosymbolic)",
    "SME ESG Feasibility",
    "Real-Time ESG Intelligence",
    "ESG Sentiment & Risk",

    # Papers
    "Paper 1: Carbonwashing Triangulation",
    "Paper 2: Neurosymbolic ESG Scoring",
    "Paper 4: SME Credit Risk (Causal ESG)",
    "Paper 3: KG-RAG Real-Time ESG"
]

source = [
    0, 0, 0,            # Greenwashing → RQs
    1, 1,               # Transparency → RQs
    2, 2, 2,            # Tech → RQs
    3, 3,               # Finance → RQs

    4, 5, 6,            # RQs → Paper 1
    7, 8,               # RQs → Paper 2
    9, 10,              # RQs → Paper 3
    11                  # RQs → Paper 4
]

target = [
    4, 5, 6,
    7, 8,
    8, 9, 11,
    10, 11,

    12, 12, 12,
    13, 13,
    14, 14,
    15
]

value = [
    3, 2, 3,
    3, 3,
    2, 2, 3,
    2, 3,

    3, 2, 3,
    3, 3,
    3, 2,
    4
]

fig = go.Figure(data=[go.Sankey(
    node=dict(label=labels, pad=15, thickness=20),
    link=dict(source=source, target=target, value=value)
)])

fig.update_layout(
    title_text="Sankey Diagram: Research Themes → RQs → ESG Research Projects",
    font_size=11
)

fig.show()
```

---

## 4️⃣ How You Can Use This in Writing

You can **explicitly reference the Sankey** in your proposal:

> *“Figure X illustrates how high-level ESG research themes are operationalized into concrete research questions and subsequently instantiated as four coherent research projects. The Sankey structure highlights methodological convergence, thematic overlap, and justified divergence across the proposed studies.”*

---

If you want next:

* 🔹 A **LaTeX/TikZ version**
* 🔹 A **Streamlit app page**
* 🔹 A **PhD proposal paragraph explaining the Sankey**
* 🔹 A **reviewer-proof justification narrative**

Just tell me which one you want to tackle next.


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
