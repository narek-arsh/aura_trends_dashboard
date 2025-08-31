import streamlit as st
import yaml

def render_filters():
    with open("config/categories.yaml", "r", encoding="utf-8") as f:
        categories = yaml.safe_load(f)

    category_names = ["Todas"] + categories
    selected = st.radio("Filtrar por categoría", category_names, horizontal=True)
    return selected
# Filtros por categoría
