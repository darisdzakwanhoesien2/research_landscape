1. https://chatgpt.com/c/695bbb2f-5644-8327-9c13-76501da9e35b
2. https://chatgpt.com/c/695bfa94-94b8-8332-8f38-55c3e68a33ec

Perfect — here’s a **planning table structure** you can use as the **input control layer** for your modular LaTeX + batch prompt workflow (NotebookLM / Streamlit / CLI).

I’ll give you:

1. ✅ A **conceptual table (Markdown)** for human planning
2. ✅ A **CSV-ready schema** for automation
3. ✅ Example rows filled with **your 4 research questions**

---

# ✅ 1. CONCEPTUAL INPUT TABLE (FOR PLANNING)

| section_name | section_part | part_title                            | research_question                                                                                                                        | batch_id | notes                       |
| ------------ | ------------ | ------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- | -------- | --------------------------- |
| Introduction | 1            | ESG & SME Reporting Context           | How does the integration of FinBERT-based tone analysis improve detection of greenwashing in SME self-assessments vs standard sentiment? | RQ1_B1   | Market + regulatory context |
| Introduction | 2            | Greenwashing via Linguistic Framing   | How does the integration of FinBERT-based tone analysis improve detection of greenwashing in SME self-assessments vs standard sentiment? | RQ1_B1   | Disclosure strategies       |
| Introduction | 3            | Limits of Generic Sentiment Models    | How does the integration of FinBERT-based tone analysis improve detection of greenwashing in SME self-assessments vs standard sentiment? | RQ1_B1   | Motivation for FinBERT      |
| Methods      | 1            | Financial Tone Modeling (FinBERT)     | How does the integration of FinBERT-based tone analysis improve detection of greenwashing in SME self-assessments vs standard sentiment? | RQ1_B2   | Model + features            |
| Methods      | 2            | Tone–Evidence Mismatch Signals        | How does the integration of FinBERT-based tone analysis improve detection of greenwashing in SME self-assessments vs standard sentiment? | RQ1_B2   | Detection logic             |
| Methods      | 1            | Aspect Clustering Pipeline            | How does clustering raw aspects into high-level ESG themes improve Level-2 certification transparency?                                   | RQ2_B1   | 02_Aspects_Clustered.py     |
| Methods      | 2            | Auditable Theme Mapping               | How does clustering raw aspects into high-level ESG themes improve Level-2 certification transparency?                                   | RQ2_B1   | Traceability                |
| Evaluation   | 1            | Aspect Agreement vs Score Reliability | What is the quantitative relationship between aspect comparison and ESG score reliability?                                               | RQ3_B1   | Correlation analysis        |
| Evaluation   | 2            | Error Propagation Analysis            | What is the quantitative relationship between aspect comparison and ESG score reliability?                                               | RQ3_B1   | Confidence metrics          |
| Discussion   | 1            | Limits of Self-Assessment             | How can benchmarks provide industry context missing from self-assessment?                                                                | RQ4_B1   | Motivation                  |
| Discussion   | 2            | Benchmark-Aware Scoring               | How can benchmarks provide industry context missing from self-assessment?                                                                | RQ4_B1   | Model integration           |

This table lets you decide:

* what **section**
* what **sub-part**
* which **research question**
* which **batch of papers / evidence**

Each row = one LaTeX module to be generated.

---

# ✅ 2. CSV SCHEMA (FOR NOTEBOOKLM / STREAMLIT / PIPELINES)

This is the **recommended machine-friendly format**:

```csv

```

This works perfectly with:

* batch prompt generation
* automated `.tex` file naming:

  * `introduction_1.tex`
  * `methods_2.tex`
* section-wise BibTeX merging

---

# ✅ 3. HOW THIS MAPS TO YOUR NOTEBOOKLM PROMPT

For each **batch_id**, you feed:

* all papers relevant to that batch
* plus the rows that reference that batch

Then you use the modular prompt like:

```
SECTION NAME: Introduction
REQUIRED OUTPUT MODULES:
- Part 1: ESG & SME Reporting Context
- Part 2: Greenwashing via Linguistic Framing
- Part 3: Limits of Generic Sentiment Models
RESEARCH QUESTION: ...
PAPERS: ...
```

So:

* **table = orchestration layer**
* **NotebookLM = synthesis engine**
* **LaTeX = final assembly**

---

# 🎯 Next Step (Very Useful for You)

If you want, I can next give you:

### ✅ Option A — Prompt Auto-Builder

Python / Streamlit app that:

* reads this CSV
* groups by `batch_id`
* prints ready-to-paste NotebookLM prompts

### ✅ Option B — LaTeX Export Pipeline

Script that:

* stores each generated part as:
  `sections/{section}_{part}.tex`
* merges BibTeX automatically

### ✅ Option C — Research Traceability Matrix

Adds columns for:

* dataset used
* model used
* validation metric

Tell me which one you want and I’ll design it for your workflow.


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

https://chatgpt.com/c/695eaa59-f664-832c-bfc9-ea233782cebe

Yes — this is very doable and very useful for debugging LaTeX builds 👍
You can make a Streamlit app that:

* Uploads or reads:

  * LaTeX build **stdout log** (for example `pdflatex.out` or captured terminal output)
  * `.aux` file
* Displays them nicely with:

  * Tabs
  * Error / warning highlighting
  * Section jump links (for `.aux`)

Below is a **complete Streamlit app** you can run directly.

---

# ✅ Features

* 📤 Upload `.log` / `stdout.txt` and `.aux` files
* 📂 Or load from `data/latex/` folder
* 🔍 Highlight:

  * Errors
  * Warnings
  * Overfull boxes
* 📑 Parse `.aux`:

  * Sections
  * Labels
  * Citations

---

# ✅ Folder Structure

```
latex_viewer_app/
│
├── app.py
└── data/
    └── latex/
        ├── build_stdout.txt
        └── main.aux
```

---

# ✅ `app.py` — Complete Streamlit App

```python

```

---

# 🔥 Possible Upgrades (very useful for you)

Given your workflow with research + LaTeX + automation, next steps could be:

### ✅ 1. Compile LaTeX inside Streamlit

Run `pdflatex` and capture stdout automatically:

* upload `.tex`
* compile
* show log + aux + pdf preview

### ✅ 2. Error Line Linking

Parse:

```
l.123 \section{...
```

→ jump to line in `.tex`

### ✅ 3. BibTeX / Biber Support

Parse:

* `.bbl`
* `.blg`

to show citation failures

### ✅ 4. Build History Dashboard

Store:

* timestamps
* errors
* warnings

for regression tracking of papers.

---

If you want, next I can give you:

* ✅ Version that **runs pdflatex from Streamlit**
* ✅ Version that also previews the **compiled PDF**
* ✅ Version integrated with your **research paper prompt + LaTeX pipeline**

Just tell me which direction you want to go.

https://chatgpt.com/c/6960f160-3bac-832e-bb35-2b40d8c359b5

Great idea — this fits perfectly with your ACL pipeline 👍
Here’s a **complete Streamlit page** that:

### ✅ What this page does

* Loads JSON from:
  `data/acl_anthology_venue/acl/extracted.json`
* Parses `"links"` field
* Filters only **volume links** like:
  `/volumes/2025.acl-tutorials/`
* Converts them into **BibTeX download URLs** like:
  👉 `https://aclanthology.org/volumes/2025.acl-tutorials.bib`
* Displays:

  * Title
  * Original volume path
  * Final BibTeX URL
* Allows:

  * Copy
  * CSV export
  * Bulk download list generation

---

# ✅ Page File

Create this as:

```
pages/02_ACL_Volume_Bib_Downloader.py
```

---

# ✅ Full Streamlit Page Code

```python

```

---

# ✅ Example Output

From:

```
"/volumes/2025.acl-tutorials/"
```

You get:

```
https://aclanthology.org/volumes/2025.acl-tutorials.bib
```

Ready for:

```bash
wget https://aclanthology.org/volumes/2025.acl-tutorials.bib
```

or batch processing into your BibTeX search dashboard.

---

# 🔥 Next-Level Upgrade (very useful for you)

If you want, next I can add:

### ✅ Bulk Downloader Page

* fetch all BibTeX files
* save to `data/acl_anthology/`
* logging (success / failed)

### ✅ Auto-pipeline

Venue JSON → volume bib → batch parse → topic clustering

Which matches perfectly with your:

* research mapping
* KG-RAG ESG project
* PhD literature pipelines

---

If you want next page, say:

👉 **“Add bulk downloader page”**
or
👉 **“Connect this to batch abstract search automatically”**
