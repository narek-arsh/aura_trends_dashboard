import streamlit as st

CATEGORIES = ["todas", "moda", "gastronomia", "arte_cultura", "lifestyle", "malaga", "guardadas"]

def category_filter():
    # Guardamos selección en session_state para estabilidad en reruns
    if "selected_category" not in st.session_state:
        st.session_state.selected_category = "todas"

    st.markdown("**Filtrar por categoría**")
    selected = st.radio(
        label="",
        options=CATEGORIES,
        horizontal=True,
        index=CATEGORIES.index(st.session_state.selected_category),
        label_visibility="collapsed",
        key="selected_category",
    )
    return selected  # siempre string
