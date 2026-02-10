# app/pages/1_Data_Library.py
import streamlit as st
from utils.csv_loader import load_csv_from_path

def app():
    st.title("Data Library")

    # Define the path (could also use config/settings.py)
    data_path = "data/csv/2024.findings-acl.csv"

    try:
        df = load_csv_from_path(data_path)  # Loads CSV into DataFrame
        st.dataframe(df)  # Display raw table
        st.write("---")
        st.markdown(f"**File Path:** `{data_path}`")

    except FileNotFoundError:
        st.error("CSV file not found! Check the path.")
