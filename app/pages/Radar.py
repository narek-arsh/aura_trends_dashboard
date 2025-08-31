import streamlit as st
import json
import os
from app.components.card import render_card

st.set_page_config(page_title="📡 Radar", layout="wide")
st.title("📡 Radar de Tendencias")

if not os.path.exists("data/trends.json"):
    st.warning("No hay datos disponibles aún.")
else:
    with open("data/trends.json", "r", encoding="utf-8") as f:
        items = json.load(f)

    sort_option = st.selectbox("Ordenar por", ["Fecha reciente", "Score"])
    if sort_option == "Score":
        items = sorted(items, key=lambda x: x.get("score", 0), reverse=True)
    else:
        items = sorted(items, key=lambda x: x.get("published", ""), reverse=True)

    col1, col2 = st.columns(2)
    for i, item in enumerate(items):
        with (col1 if i % 2 == 0 else col2):
            render_card(item)