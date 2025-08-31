import streamlit as st

def render_cards(trend):
    st.markdown("---")
    st.markdown(f"### {trend['title']}")
    st.markdown(f"**Categoría:** {trend.get('categoria', 'Sin categoría')}")
    st.markdown(f"{trend.get('summary', '')}")
    st.markdown(f"🔍 _Why it matters:_ {trend.get('why_it_matters', '')}")
    st.markdown(f"💡 _Ideas de activación:_ {trend.get('ideas_activacion', '')}")
    st.markdown(f"[🌐 Ver noticia original]({trend.get('link')})")
# Lógica de visualización de tarjetas de noticias
