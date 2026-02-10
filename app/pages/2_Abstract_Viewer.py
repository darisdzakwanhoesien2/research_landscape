# app/pages/2_Abstract_Viewer.py
import streamlit as st
from utils.csv_loader import load_csv_from_path

def app():
    st.title("Abstract Viewer")

    # Load and preprocess data
    df = load_csv_from_path("data/csv/2024.findings-acl.csv")
    df["abstract_summary"] = df.apply(
        lambda row: f"**{row['author']}** ({row['journal']}):\n{row['abstract'][:500]}...",
        axis=1
    )

    # Display in a table with expandable rows
    for _, row in df.iterrows():
        st.markdown(row["abstract_summary"])
        st.divider()  # Separate abstracts visually

