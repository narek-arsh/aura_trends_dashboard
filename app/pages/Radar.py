import json
import streamlit as st
from app.components.filters import category_filter
from app.components.card import render_article
from app.components.weather import render_weather
from app.utils.storage import get_saved

st.set_page_config(page_title="Aura Dashboard", layout="wide")

def _load_trends(path: str = "data/trends.json"):
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f) or []
            return data if isinstance(data, list) else []
    except Exception:
        return []

def _columns(spec):
    try:
        return st.columns(spec, gap="large")
    except TypeError:
        return st.columns(spec)

def main():
    st.title("Aura Dashboard")
    render_weather()

    selected = category_filter()  # siempre string por filters.py
    if selected == "guardadas":
        articles = get_saved()
    else:
        articles = _load_trends()
        if selected != "todas":
            s = (selected or "todas").lower()
            articles = [a for a in articles if (a.get("category") or "").lower() == s]

        if not articles:
        st.info("Aún no hay artículos para mostrar. Cuando el colector procese nuevos, aparecerán aquí.")
        return

    # Mostrar primero las noticias más recientes
    articles = list(reversed(articles))

    left, right = _columns(2)
    for i, art in enumerate(articles):
        with (left if i % 2 == 0 else right):
            render_article(art)
            st.markdown("---")
