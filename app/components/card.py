import streamlit as st
from bs4 import BeautifulSoup

def _extract_image_and_text(summary_html: str):
    """
    Del HTML del summary (RSS) saca:
      - primera imagen (si existe)
      - texto limpio (sin etiquetas)
    """
    if not summary_html:
        return None, ""

    try:
        soup = BeautifulSoup(summary_html, "html.parser")

        # Imagen: primera <img>
        img_url = None
        img_tag = soup.find("img")
        if img_tag and img_tag.get("src"):
            img_url = img_tag.get("src")

        # Texto visible, sin etiquetas ni scripts
        for tag in soup(["script", "style"]):
            tag.extract()
        text = soup.get_text(separator=" ", strip=True)

        return img_url, text
    except Exception:
        return None, summary_html

def render_article(article: dict):
    """
    Tarjeta con:
      - Título
      - Categoría
      - Imagen (si la hay)
      - Resumen limpio (recortado)
      - Campos IA (opcionales)
      - Link a la noticia original
    """
    title = article.get("title", "Sin título")
    category = article.get("category") or "Sin categoría"
    link = article.get("link", "")
    summary_html = article.get("summary", "")

    img_url, clean_text = _extract_image_and_text(summary_html)
    max_chars = 280
    short_text = (clean_text[:max_chars] + "…") if len(clean_text) > max_chars else clean_text

    with st.container(border=True):
        st.markdown(f"### {title}")
        st.caption(f"**Categoría:** {category}")

        col_img, col_txt = st.columns([1, 2], gap="large")
        with col_img:
            if img_url:
                st.image(img_url, use_container_width=True)  # ← actualizado
        with col_txt:
            if short_text:
                st.write(short_text)

        why = article.get("why_it_matters")
        ideas = article.get("activation_ideas")
        if why:
            st.markdown("#### 🔎 Why it matters:")
            st.write(why)
        if ideas:
            st.markdown("#### 💡 Ideas de activación:")
            st.write(ideas)

        if link:
            st.markdown(f"[🌐 Ver noticia original]({link})")
