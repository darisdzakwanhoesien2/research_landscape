import re
import json
from pathlib import Path
import pandas as pd

# ============================================================
# INPUT RAW TEXT
# ============================================================

RAW_TEXT = """
• 3 / source3: Comprehensive Integrated Objectives (With Provenance & Reasoning).
• 4 / source4: Integrated Mapping of Hypothesis, Objectives, Research Gaps, and Problems.
• 5 / source5: Problem-Gap-RQ-Objective Matrix and Reasoning.
• 6 / source6: Integrated Mapping of Objective Layers, Research Gaps, and Questions.
• 9: One-Line Unified Master Objective (Thesis-Level).
• source12: Gradio-based interface for ESG Data ([[gradio-esgdata]]).
• source14: Research Gap Reference Index (Linking Gaps G1–G4 to Source Files).
• 17 / source17: Objective Layer 1 — ESG Data, Semantics & Multilingual Foundations.
• 18 / source18: Aligned Research Questions for Objective Layer 1.
• source20: Aligned Research Questions for Objective Layer 2.
• source22: Objective Layer 3 — Reasoning, Explainability & Semantic Alignment.
• source23: Aligned Research Questions for Objective Layer 3.
• 25 / source25: Objective Layer 4 — Trust, Risk & Greenwashing Intelligence.
• 26 / source26: Aligned Research Questions for Objective Layer 4.
• 28: Aligned Research Questions for Objective Layer 5.
• 32 / source32: Problem P1 — Lack of Fine-Grained ESG Sentiment Understanding.
• 33 / source33: Aligned Research Questions for Problem Statement P1.
• 34 / source34: Problem P2 — Structural, Tonal & Ontological Modeling Limitations.
• 36 / source36: Research Objectives addressing Problem Statement P2.
• 37 / source37: Problem P3 — Narrative Complexity & Greenwashing Detection Limitations.
• 39 / source39: Problem P4 — Scalability & Contextual Coherence in Long Documents.
• 40 / source40: Derived Research Gap G4 — Need for scalable long-context DL-ABSA frameworks.
• 42: End-to-End Traceability Matrix (Condensed Condensed Problem-Gap-RQ-Objective mapping).
--------------------------------------------------------------------------------
Literature Research Papers
• source44: Improving Neural Political Statement Classification with Class Hierarchical Information.
• source46: BiSyn-GAT+: Bi-Syntax Aware Graph Attention Network for Aspect-based Sentiment Analysis.
• source49: Incorporating Dynamic Semantics into Pre-Trained Language Model for Aspect-based Sentiment Analysis.
• source50: Seq2Path: Generating Sentiment Tuples as Paths of a Tree.
• source55: Towards Unifying the Label Space for Aspect- and Sentence-based Sentiment Analysis.
• 56 / source56: Attention Mechanism with Energy-Friendly Operations.
• source57: Graph-Guided Textual Explanation Generation Framework.
• source58: s1: Simple test-time scaling.
• source59: FinMTEB: Finance Massive Text Embedding Benchmark.
• source60: M-ABSA: A Multilingual Dataset for Aspect-Based Sentiment Analysis.
• source61: Facilitating Long Context Understanding via Supervised Chain-of-Thought Reasoning.
• 62 / source62: Two Heads Are Better Than One: Dual-Model Verbal Reflection at Inference-Time.
• source65: What Makes a Good Reasoning Chain? Uncovering Structural Patterns in Long Chain-of-Thought Reasoning.
• source68: ESGenius: Benchmarking LLMs on Environmental, Social, and Governance (ESG) and Sustainability Knowledge.
• 69 / source69: Measuring Chain of Thought Faithfulness by Unlearning Reasoning Steps.
• 71 / source71: Analysing Chain of Thought Dynamics: Active Guidance or Unfaithful Post-hoc Rationalisation?.
• source74: Reward Model Perspectives: Whose Opinions Do Reward Models Reward?.
• source75: Comprehensive and Efficient Distillation for Lightweight Sentiment Analysis Models.
• source77: DICE: Structured Reasoning in LLMs through SLM-Guided Chain-of-Thought Correction.
• source82: Towards AI-Assisted Psychotherapy: Emotion-Guided Generative Interventions.
• 83 / source83: TokenSkip: Controllable Chain-of-Thought Compression in LLMs.
• 85 / source85: SSA: Semantic Contamination of LLM-Driven Fake News Detection.
• source91: RD-MCSA: A Multi-Class Sentiment Analysis Approach Integrating In-Context Classification Rationales and Demonstrations.
• source93: Knowledge Editing through Chain-of-Thought.
• source94: Look Beyond Feeling: Unveiling Latent Needs from Implicit Expressions for Proactive Emotional Support.
• source95: TracSum: A New Benchmark for Aspect-Based Summarization with Sentence-Level Traceability in Medical Domain.
• source97: Long Chain-of-Thought Fine-tuning via Understanding-to-Reasoning Transition.
• 100 / source100: NOVA-63: Native Omni-lingual Versatile Assessments of 63 Disciplines.
• source101: Parallel Continuous Chain-of-Thought with Jacobi Iteration.
• 102 / source102: A Systematic Survey of Automatic Prompt Optimization Techniques.
• source103: Internal Chain-of-Thought: Empirical Evidence for Layer-wise Subtask Scheduling in LLMs.
• 104 / source104: From Long to Lean: Performance-aware and Adaptive Chain-of-Thought Compression via Multi-round Refinement.
• source107: CODI: Compressing Chain-of-Thought into Continuous Space via Self-Distillation.
• source109: Diagnosing Memorization in Chain-of-Thought Reasoning, One Token at a Time.
• 112 / source112: DS 2 -ABSA: Dual-Stream Data Synthesis with Label Refinement for Few-Shot Aspect-Based Sentiment Analysis.
• source114: CoT-ICL Lab: A Synthetic Framework for Studying Chain-of-Thought Learning from In-Context Demonstrations.
• source115: Fine-Tuning on Diverse Reasoning Chains Drives Within-Inference CoT Refinement in LLMs.
• source116: A Theory of Response Sampling in LLMs: Part Descriptive and Part Prescriptive.
• source118: Enhancing Chain-of-Thought Reasoning with Critical Representation Fine-tuning.
• source124: LACA: Improving Cross-lingual Aspect-Based Sentiment Analysis with LLM Data Augmentation.
• source125: Know Your Mistakes: Towards Preventing Overreliance on Task-Oriented Conversational AI Through Accountability Modeling.
• 126 / source126: Improving Chain-of-Thought Reasoning via Quasi-Symbolic Abstractions.
• source128: Hierarchical Sequence Labeling Model for Aspect Sentiment Triplet Extraction.
• source130: Self-Harmonized Chain of Thought.
• source131: Markov Chain of Thought for Efficient Mathematical Reasoning.
• 132 / source132: On the Impact of Fine-Tuning on Chain-of-Thought Reasoning.
• 133 / source133: Test-Time Code-Switching for Cross-lingual Aspect Sentiment Triplet Extraction.
• source136: Single Ground Truth Is Not Enough: Adding Flexibility to Aspect-Based Sentiment Analysis Evaluation.
• 138 / source138: Verify-in-the-Graph: Entity Disambiguation Enhancement for Complex Claim Verification with Interactive Graph Representation.
• 139 / source139: EmoDynamiX: Emotional Support Dialogue Strategy Prediction by Modelling MiXed Emotions and Discourse Dynamics
"""

# ============================================================
# OUTPUT PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[1]
OUT_JSON = BASE_DIR / "data" / "source_registry.json"
OUT_CSV = BASE_DIR / "data" / "source_registry.csv"

OUT_JSON.parent.mkdir(parents=True, exist_ok=True)

# ============================================================
# REGEX
# ============================================================

BULLET_RE = re.compile(
    r"•\s*(?:(\d+)\s*/\s*)?(source\d+)?\s*:\s*(.+)",
    re.IGNORECASE
)

WIKI_LINK_RE = re.compile(r"\[\[(.*?)\]\]")

# ============================================================
# PARSER
# ============================================================

def parse_sources(raw_text: str):
    records = []
    current_section = "research-artifacts"

    for line in raw_text.splitlines():
        line = line.strip()

        if not line:
            continue

        if "Literature Research Papers" in line:
            current_section = "literature"
            continue

        m = BULLET_RE.search(line)
        if not m:
            continue

        numeric_id = m.group(1)
        source_id = m.group(2)
        title = m.group(3).strip().rstrip(".")

        wiki_links = WIKI_LINK_RE.findall(title)
        title_clean = WIKI_LINK_RE.sub("", title).strip()

        # Normalize source id
        if not source_id and numeric_id:
            source_id = f"source{numeric_id}"

        if not source_id:
            continue

        record = {
            "source_id": source_id.lower(),
            "numeric_id": int(numeric_id) if numeric_id else None,
            "title": title_clean,
            "section": current_section,
            "wiki_links": wiki_links,
        }

        records.append(record)

    return records

# ============================================================
# SAVE
# ============================================================

def main():
    records = parse_sources(RAW_TEXT)

    df = pd.DataFrame(records).sort_values("source_id")

    # JSON format (dictionary by source_id)
    registry = {
        r["source_id"]: {
            "numeric_id": r["numeric_id"],
            "title": r["title"],
            "section": r["section"],
            "wiki_links": r["wiki_links"],
        }
        for r in records
    }

    OUT_JSON.write_text(json.dumps(registry, indent=2, ensure_ascii=False))
    df.to_csv(OUT_CSV, index=False)

    print(f"✅ Parsed {len(records)} sources")
    print(f"📄 JSON saved → {OUT_JSON}")
    print(f"📄 CSV saved  → {OUT_CSV}")

if __name__ == "__main__":
    main()
