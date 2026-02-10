# app/main_app.py
import streamlit as st

def main():
    st.set_page_config(layout="wide")
    st.title("Abstract Analyzer Dashboard")

    tab1, tab2 = st.tabs(["Data Library", "Abstract Viewer"])
    with tab1:
        from .pages import Data_Library  # Import page functions
        Data_Library.app()
    with tab2:
        from .pages import Abstract_Viewer
        Abstract_Viewer.app()

if __name__ == "__main__":
    main()
