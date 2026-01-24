import streamlit as st
import pandas as pd

st.title("🔍 Search & Filter")

if "clean_df" not in st.session_state:
    st.warning("Please consolidate data first.")
    st.stop()

df = st.session_state["clean_df"]

query = st.text_input("Search title / abstract / authors")

if query:
    mask = (
        df["title"].str.contains(query, case=False, na=False) |
        df["abstract"].str.contains(query, case=False, na=False) |
        df["authors"].str.contains(query, case=False, na=False)
    )
    df = df[mask]

year_range = st.slider(
    "Year range",
    min_value=1900,
    max_value=2030,
    value=(2000, 2030)
)

df = df[
    (df["year"].astype(str).str.extract("(\d+)")[0].astype(float) >= year_range[0]) &
    (df["year"].astype(str).str.extract("(\d+)")[0].astype(float) <= year_range[1])
]

st.write(f"Results: {len(df)}")
st.dataframe(df, use_container_width=True)
