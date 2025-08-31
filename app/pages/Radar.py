import streamlit as st
from app.components.weather import render_weather
from app.components.filters import render_filters
from app.components.card import render_cards
import json
import os

st.set_page_config(page_title="Radar de Tendencias", layout="wide")

render_weather()
selected_category = render_filters()

# Cargar noticias
data_path = "data/trends.json"
if os.path.exists(data_path):
    with open(data_path, "r", encoding="utf-8") as f:
        all_trends = json.load(f)
else:
    all_trends = []

# Filtro
if selected_category and selected_category != "Todas":
    filtered = [item for item in all_trends if item.get("categoria") == selected_category]
else:
    filtered = all_trends

# Tarjetas en dos columnas
col1, col2 = st.columns(2)

for i, trend in enumerate(filtered):
    with col1 if i % 2 == 0 else col2:
        render_cards(trend)
# Página principal con el radar de noticias
