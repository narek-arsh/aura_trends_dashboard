import streamlit as st
import json
import os
from app.components.card import render_cards

st.set_page_config(page_title="Guardadas", layout="wide")
st.title("🗂 Noticias guardadas")

# Cargar noticias guardadas
data_path = "data/trends.json"
if os.path.exists(data_path):
    with open(data_path, "r", encoding="utf-8") as f:
        saved = json.load(f)
else:
    saved = []

# Mostrar en dos columnas
col1, col2 = st.columns(2)

for i, trend in enumerate(saved):
    with col1 if i % 2 == 0 else col2:
        render_cards(trend)
# Página de noticias guardadas
