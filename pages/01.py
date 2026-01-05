import streamlit as st
import plotly.graph_objects as go

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="Research Mapping – Sankey Diagram",
    layout="wide"
)

st.title("🔗 Research Mapping: Themes → Research Questions → Projects")
st.caption(
    "Visualizing how high-level ESG research themes are operationalized "
    "into research questions and instantiated as concrete research projects."
)

st.divider()

# ============================================================
# EXPLANATORY CONTEXT
# ============================================================
with st.expander("📘 How to Read This Diagram", expanded=True):
    st.markdown(
        """
        **This Sankey diagram represents the intellectual flow of the research project:**

        - **Left:** High-level *research themes* motivating the work  
        - **Middle:** Concrete *research questions (RQs)* derived from those themes  
        - **Right:** Implemented *research projects / papers*

        **Flow thickness** represents conceptual relevance and strength of linkage,  
        not statistical weight.

        This structure demonstrates:
        - Conceptual coherence  
        - Methodological justification  
        - Non-overlapping yet complementary research outputs
        """
    )

# ============================================================
# SANKEY DATA
# ============================================================
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

    # Research Projects
    "Paper 1: Carbonwashing Triangulation",
    "Paper 2: Neurosymbolic ESG Scoring",
    "Paper 3: SME Credit Risk (Causal ESG)",
    "Paper 4: KG-RAG Real-Time ESG"
]

source = [
    # Themes → RQs
    0, 0, 0,            # Greenwashing
    1, 1,               # Transparency
    2, 2, 2,            # Tech
    3, 3,               # Finance

    # RQs → Papers
    4, 5, 6,            # → Paper 1
    7, 8,               # → Paper 2
    9, 10,              # → Paper 3
    11                  # → Paper 4
]

target = [
    # Themes → RQs
    4, 5, 6,
    7, 8,
    8, 9, 11,
    10, 11,

    # RQs → Papers
    12, 12, 12,
    13, 13,
    14, 14,
    15
]

value = [
    # Themes → RQs
    3, 2, 3,
    3, 3,
    2, 2, 3,
    2, 3,

    # RQs → Papers
    3, 2, 3,
    3, 3,
    3, 2,
    4
]

# ============================================================
# SANKEY FIGURE
# ============================================================
fig = go.Figure(
    data=[
        go.Sankey(
            arrangement="snap",
            node=dict(
                label=labels,
                pad=18,
                thickness=22,
                line=dict(color="black", width=0.5)
            ),
            link=dict(
                source=source,
                target=target,
                value=value
            )
        )
    ]
)

fig.update_layout(
    title="Sankey Diagram: ESG Research Logic Flow",
    font_size=12,
    height=700
)

st.plotly_chart(fig, use_container_width=True)

st.divider()

# ============================================================
# INTERPRETATION SECTION
# ============================================================
st.subheader("🧠 Interpretation & Research Justification")

col1, col2 = st.columns(2)

with col1:
    st.markdown(
        """
        **Why this structure matters:**

        - Prevents *topic fragmentation*
        - Makes thesis contributions explicit
        - Shows why projects are **complementary, not redundant**
        - Aligns methodological choices with research intent

        Each project answers **distinct but connected questions**, 
        ensuring academic depth without overlap.
        """
    )

with col2:
    st.markdown(
        """
        **Key Design Principle:**

        > Themes motivate  
        > Research questions operationalize  
        > Projects implement  

        This ensures traceability from **theory → method → contribution**, 
        a requirement in PhD proposals, ERC-style grants, and journal roadmaps.
        """
    )

# ============================================================
# OPTIONAL EXPORT
# ============================================================
with st.expander("⬇️ Export / Reuse"):
    st.markdown(
        """
        - This diagram can be referenced directly in:
          - PhD proposals
          - Thesis introduction chapters
          - Research roadmaps
          - Grant applications

        - If needed, it can be exported as:
          - Static figure (PNG / PDF)
          - Interactive HTML
          - LaTeX/TikZ recreation
        """
    )
