import streamlit as st

CATEGORIES = ["todas", "moda", "gastronomia", "arte_cultura", "lifestyle", "malaga", "guardadas"]

def category_filter():
    st.markdown("**Filtrar por categoría**")
    selected = st.radio(
        label="",
        options=CATEGORIES,
        horizontal=True,
        index=0,
        label_visibility="collapsed",
    )
    return selected  # incluye 'guardadas'
