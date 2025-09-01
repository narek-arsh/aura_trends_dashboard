import streamlit as st
from app.utils.storage import get_saved
from app.components.card import render_article

st.set_page_config(page_title="Guardadas", layout="wide")
st.title("🗂 Noticias guardadas")

saved = get_saved()

if not saved:
    st.info("Todavía no tienes noticias guardadas. En el Radar puedes marcar ⭐ Guardar en cualquier tarjeta.")
else:
    col1, col2 = st.columns(2, gap="large")
    for i, art in enumerate(saved):
        with (col1 if i % 2 == 0 else col2):
            render_article(art)
            st.markdown("---")
