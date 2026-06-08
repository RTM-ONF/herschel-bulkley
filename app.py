import streamlit as st

main_page = st.Page("main.py", title="Accueil")

pg = st.navigation([main_page])

pg.run()