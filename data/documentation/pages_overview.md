# 📘 Application Page Documentation

## 📄 Research Landscape Explorer

**File:** `app.py`

**Purpose**  
Acts as the central dashboard to visualize academic metadata using knowledge maps, word cloud analysis, and bibliometrics to compare journals and conference papers.

**Inputs**  
Academic metadata from WoS, Scopus, OpenAlex, or Semantic Scholar in CSV/JSON format.

**Outputs / Visuals**  
Interactive word clouds, keyword co-occurrence knowledge graphs, and temporal topic evolution charts.

**When to use**  
Exploration and PRISMA-adjacent systematic landscape analysis.

---

## 📄 PhD Mapping and Project Traceability

**File:** `pages/01_PhD_Mapping.py`

**Purpose**  
Visualizes the flow between high-level research themes, specific research questions, and individual research papers using a multi-layer Sankey structure.

**Inputs**  
Research themes, research questions, and project target lists (Paper 1-4).

**Outputs / Visuals**  
Plotly-based Sankey diagrams illustrating methodological convergence and justified divergence.

**When to use**  
Research design, project exploration, and proposal writing.

---

## 📄 NotebookLM Prompt Orchestrator

**File:** `pages/03_NotebookLM_Master.py`

**Purpose**  
Orchestrates the synthesis process by grouping relevant research papers by batch_id to generate structured prompts for the NotebookLM synthesis engine.

**Inputs**  
CSV data containing paper references and batch identifiers.

**Outputs / Visuals**  
Ready-to-paste prompts tailored for batch-wise research synthesis.

**When to use**  
Preprocessing and prompt engineering for synthesis tasks.

---

## 📄 LaTeX Build and Aux Analysis

**File:** `pages/05_aux.py`

**Purpose**  
Analyzes LaTeX build logs and auxiliary files to provide debugging insights and document structural verification.

**Inputs**  
LaTeX .log files, stdout.txt, and .aux files.

**Outputs / Visuals**  
Highlighted lists of errors, warnings, overfull boxes, and parsed tables of document labels and citations.

**When to use**  
Debugging and document verification during the reporting phase.

---

## 📄 LaTeX Converter with Hallucination Mitigation

**File:** `pages/08_latex_converter_with_hallucination_mitigation.py`

**Purpose**  
Transforms generated research content into LaTeX format while implementing validation checks to ensure citation accuracy and reduce model hallucinations.

**Inputs**  
Raw research text and associated BibTeX citation keys.

**Outputs / Visuals**  
Validated, LaTeX-ready .tex files with grounded citations.

**When to use**  
Reporting and final assembly with quality control.

---

## 📄 ACL Anthology BibTeX Linker

**File:** `pages/10_acl_anthology.py`

**Purpose**  
Parses extracted volume links from the ACL Anthology and converts them into standardized BibTeX download URLs.

**Inputs**  
extracted.json from ACL Anthology venue data.

**Outputs / Visuals**  
Searchable tables of volume titles, original paths, and functional BibTeX URLs for bulk download list generation.

**When to use**  
Literature search and bibliographic data gathering.

---

## 📄 ACL Volume Bib Downloader

**File:** `pages/12_ACL_Volume_Bib_Downloader.py`

**Purpose**  
Performs automated batch retrieval of BibTeX files for identified ACL Anthology volumes to populate local research databases.

**Inputs**  
Generated lists of ACL BibTeX download URLs.

**Outputs / Visuals**  
Local .bib files stored in the data/acl_anthology/ directory and success/failure logs.

**When to use**  
Data acquisition and bibliographic preprocessing.

---

## 📄 Keyword Co-occurrence Analysis

**File:** `pipeline/cooccurrence.py`

**Purpose**  
Processes cleaned academic metadata to calculate relationship strengths between keywords for knowledge mapping.

**Inputs**  
Cleaned and normalized keyword data from the research pipeline.

**Outputs / Visuals**  
Relationship matrices and edge data for network visualization.

**When to use**  
Preprocessing and intermediate modeling stage.

---

## 📄 Interactive Network Visualization

**File:** `viz/network.py`

**Purpose**  
Generates interactive graphical representations of research keyword relationships to identify thematic clusters.

**Inputs**  
Co-occurrence data and node-edge relationship matrices.

**Outputs / Visuals**  
Interactive Plotly or NetworkX visualizations of knowledge graphs.

**When to use**  
Exploration and thematic evaluation.

---

## 📄 Research Flow Sankey Visualization

**File:** `0_0_2.py`

**Purpose**  
Visualizes the hierarchical flow between research themes, specific research questions (RQs), and implementation papers using an interactive Sankey diagram to demonstrate project coherence.

**Inputs**  
Mapping data from 0_0_mapping_data.py and thematic link definitions.

**Outputs / Visuals**  
Interactive Plotly-based Sankey diagrams illustrating the flow from themes to papers.

**When to use**  
Research design and proposal stage to visualize methodological convergence and thematic overlap.

---

## 📄 Research Mapping Markdown Export

**File:** `0_0_3_markdown_exports.py`

**Purpose**  
Exports structured research mapping data into formatted Markdown files for use in thesis documentation, proposals, or collaborative reports.

**Inputs**  
Internal research mapping dataframes and traceability matrix structures.

**Outputs / Visuals**  
Markdown files (.md) summarizing the research hierarchy, themes, and question-paper alignments.

**When to use**  
Reporting and documentation stage of the research project.

---

## 📄 Enriched Global Research Mapping

**File:** `0_0_4_enriched_global_mapping.py`

**Purpose**  
Enriches the core research mapping with technical metadata, including datasets used, specific models employed, and validation metrics for each paper project.

**Inputs**  
Base research mapping structures and technical performance CSV files.

**Outputs / Visuals**  
A comprehensive, enriched global traceability matrix suitable for technical audits.

**When to use**  
Modeling and validation audit stage to ensure technical traceability.

---

## 📄 Research Mapping Data Core

**File:** `0_0_mapping_data.py`

**Purpose**  
Serves as the primary data definition layer for the research hierarchy, hardcoding the relationships between Themes, RQs, and Paper projects.

**Inputs**  
Hardcoded theme and research question definitions based on project requirements.

**Outputs / Visuals**  
Structured dictionaries and data objects utilized by downstream visualization and export modules.

**When to use**  
Initial project setup and structural configuration phase.

---

## 📄 Research Question to Paper Mapper

**File:** `0_0_research_question_paper_mapping.py`

**Purpose**  
Maps granular inquiry lines to corresponding implementation papers to ensure every research question is addressed by a specific project phase.

**Inputs**  
List of research questions and high-level paper descriptions.

**Outputs / Visuals**  
Alignment tables and verification reports mapping questions to paper IDs.

**When to use**  
Research design and methodological mapping phase.

---

## 📄 Condensed RQ-Paper Utility

**File:** `0_0_rq_paper_mapping.py`

**Purpose**  
Provides a condensed, lightweight mapping utility for quick association between research questions and paper projects for use in UI components.

**Inputs**  
Mapping data structures from 0_0_mapping_data.py.

**Outputs / Visuals**  
Simplified lookup tables and mapping indices for research question associations.

**When to use**  
Quick reference during writing and prompt engineering tasks.

---

## 📄 ACL Anthology Data Schema

**File:** `0_acl.py`

**Purpose**  
Defines baseline data paths and ingestion schemas for handling ACL Anthology venue and volume metadata across the application.

**Inputs**  
Configuration files and standard directory paths for ACL Anthology data.

**Outputs / Visuals**  
Standardized path objects and configuration variables for ACL-related pages.

**When to use**  
Infrastructure configuration and initialization for literature processing.

---

## 📄 Central Data Loader

**File:** `0_data.py`

**Purpose**  
Acts as the primary data ingestion utility, providing shared loading functions for CSV and JSON datasets used across the analytical modules.

**Inputs**  
Local data directory files including CSV/JSON metadata and bibliometric exports.

**Outputs / Visuals**  
Cleaned DataFrames and data structures for Streamlit app state management.

**When to use**  
Initial application boot and universal data ingestion stage.

---

## 📄 Modular Prompt Templates

**File:** `0_prompt.py`

**Purpose**  
Manages and stores reusable prompt fragments and orchestration templates for synthesis, tone analysis, and LaTeX conversion tasks.

**Inputs**  
Contextual research metadata and section-specific content strings.

**Outputs / Visuals**  
Structured text prompts designed for synthesis engines like NotebookLM or LLM-based converters.

**When to use**  
Prompt engineering and research synthesis orchestration phase.

---

## 📄 ACL Bulk BibTeX Linker

**File:** `11_bulk_bib_acl_anthology.py`

**Purpose**  
Processes extracted ACL Anthology venue JSON files to generate standardized BibTeX download URLs for all identified volumes.

**Inputs**  
extracted.json metadata files from ACL Anthology venue directories.

**Outputs / Visuals**  
Searchable tables and exportable CSV lists of functional BibTeX download URLs.

**When to use**  
Literature search and bibliographic data gathering stage.

---

## 📄 ACL Metadata Preview Dashboard

**File:** `1_ACLAnthology_Upload_and_Preview.py`

**Purpose**  
Provides an interface for uploading raw ACL Anthology metadata and previewing the extracted papers and volume links before processing.

**Inputs**  
User-uploaded JSON files from ACL Anthology venue scrapers.

**Outputs / Visuals**  
Interactive data previews and summary metrics for conference venues.

**When to use**  
Initial data ingestion and exploratory literature review stage.

---

## 📄 ACL Data Cleaning and Download

**File:** `2_ACLAnthology_Clean_and_Download.py`

**Purpose**  
Cleans volume links and automates the batch retrieval of BibTeX files for identified ACL Anthology volumes.

**Inputs**  
Filtered volume lists and BibTeX URLs generated by upstream ACL pages.

**Outputs / Visuals**  
Local .bib files saved to data directories and batch download status logs.

**When to use**  
Preprocessing and data acquisition phase for bibliography building.

---

## 📄 NotebookLM Prompt Orchestrator

**File:** `2_json_to_notebooklm_prompt.py`

**Purpose**  
Orchestrates the synthesis process by grouping relevant paper metadata by batch ID to generate structured, ready-to-paste prompts for NotebookLM.

**Inputs**  
CSV metadata containing paper references and unique batch identifiers.

**Outputs / Visuals**  
Formatted synthesis prompts tailored for batch-wise research evaluation.

**When to use**  
Preprocessing and synthesis stage for automated research evaluation.

---

## 📄 Unified ACL Literature Dashboard

**File:** `3_ACL_combined.py`

**Purpose**  
Integrates cleaned ACL metadata with existing research mappings to provide a unified landscape view of the academic field.

**Inputs**  
Cleaned ACL bibliometric data and research project mapping CSVs.

**Outputs / Visuals**  
Integrated dashboards combining literature trends with internal research project milestones.

**When to use**  
Final reporting and landscape visualization phase.

---

## 📄 NotebookLM Prompt Builder

**File:** `02_NotebookLM.py`

**Purpose**  
Orchestrates the synthesis process by reading research CSVs and grouping papers by batch_id to generate structured, ready-to-paste prompts for the NotebookLM synthesis engine.

**Inputs**  
Research metadata CSV files containing paper descriptions and associated batch identifiers.

**Outputs / Visuals**  
Formatted, ready-to-paste text prompts tailored for batch-wise research synthesis.

**When to use**  
Preprocessing and synthesis stage to prepare research content for external LLM evaluation.

---

## 📄 Research Data Management

**File:** `04_data.py`

**Purpose**  
Provides a centralized interface for the ingestion and preliminary viewing of research datasets, including bibliometric exports and internal mapping matrices.

**Inputs**  
Local CSV/JSON files, bibliometric data, and research traceability files.

**Outputs / Visuals**  
Interactive data previews, summary statistics, and cleaned dataframes for downstream analytical modules.

**When to use**  
Data ingestion and initial exploratory stage of the research pipeline.

---

## 📄 LaTeX Section Exporter

**File:** `06_latex_converter.py`

**Purpose**  
Transforms synthesized text segments into modular LaTeX files, organizing content into structured section-wise outputs like introduction_1.tex or methods_2.tex.

**Inputs**  
Synthesized research text parts and target section identifiers.

**Outputs / Visuals**  
Modular .tex files stored in a hierarchical directory structure for final document assembly.

**When to use**  
Reporting and final assembly stage to convert raw synthesis into a structured document.

---

## 📄 Grounded LaTeX Converter

**File:** `08_latex_converter_with_hallucination_mitigation.py`

**Purpose**  
Converts research text into LaTeX while implementing automated BibTeX merging and citation validation to mitigate model hallucinations and ensure factual grounding.

**Inputs**  
Raw research text, specific BibTeX citation keys, and master .bib files.

**Outputs / Visuals**  
Validated .tex files with grounded citations and automatically merged bibliography files.

**When to use**  
Final reporting stage where rigorous citation accuracy and automated bibliography management are critical.

---

## 📄 Scraping Distribution Analysis

**File:** `09_scrapping_distribution.py`

**Purpose**  
Analyzes and visualizes the distribution of extracted academic metadata or scraped content across different research themes, venues, or temporal markers.

**Inputs**  
Scraped research datasets, venue JSON files, and extraction logs.

**Outputs / Visuals**  
Distribution charts, coverage metrics, and summary tables of the acquired research landscape.

**When to use**  
Data acquisition and preprocessing monitoring stage to ensure comprehensive literature coverage.

---
