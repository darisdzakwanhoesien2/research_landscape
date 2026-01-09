import streamlit as st
import pandas as pd

st.title("📤 Upload & Preview Raw CSV")

uploaded = st.file_uploader(
    "Upload CSV or TSV file",
    type=["csv", "tsv", "txt"]
)

sep = st.selectbox(
    "Delimiter",
    options=[",", "\t", ";", "|"],
    index=1
)

if uploaded:
    try:
        df = pd.read_csv(uploaded, sep=sep, engine="python")
        st.session_state["raw_df"] = df

        st.success(f"Loaded {df.shape[0]} rows × {df.shape[1]} columns")

        st.subheader("Column Names")
        st.code(df.columns.tolist())

        st.subheader("Preview")
        st.dataframe(df.head(20))

    except Exception as e:
        st.error(f"Failed to read file: {e}")
else:
    st.info("Please upload a CSV/TSV file.")
