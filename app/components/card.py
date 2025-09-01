import streamlit as st
from bs4 import BeautifulSoup
from app.utils.storage import is_saved, toggle_save
from hashlib import md5

def _extract_image_and_text(summary_html: str):
    if not summary_html:
        return None, ""
    try:
        soup = BeautifulSoup(summary_html, "html.parser")
        img_url = None
        img_tag = soup.find("img")
        if img_tag and img_tag.get("src"):
            img_url = img_tag.get("src")
        for tag in soup(["script", "style"]):
            tag.extract()
        text = soup.get_text(separator=" ", strip=True)
        return img_url, text
    except Exception:
        return None, summary_html

def _safe_key(s: str) -> str:
    return md5(s.encode("utf-8")).hexdigest()

def _columns(spec):
    """
    Crea columnas con soporte para versiones antiguas de Streamlit
    que no aceptan el parámetro 'gap'.
    """
    try:
        # Streamlit recientes
        return st.columns(spec, gap="large")
    except TypeError:
        # Versiones sin 'gap'
        return st.columns(spec)

def render_article(article: dict):
    title = article.get("title", "Sin título")
    category = article.get("category") or "Sin categoría"
    link = article.get("link", "")
    summary_html = article.get("summary", "")

    art_id = article.get("id") or link or title
    art_key = _safe_key(art_id)

    img_url, clean_text = _extract_image_and_text(summary_html)
    max_chars = 280
    short_text = (clean_text[:max_chars] + "…") if len(clean_text) > max_chars else clean_text

    with st.container(border=True):
        st.markdown(f"### {title}")
        st.caption(f"**Categoría:** {category}")

        col_img, col_txt = _columns([1, 2])  # ← usa helper con fallback
        with col_img:
            if img_url:
                st.image(img_url, use_container_width=True)
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
            for it in ideas:
                st.write(f"• {it}")

        saved_now = is_saved(art_id)
        btn_label = "⭐ Guardar" if not saved_now else "❌ Quitar de guardadas"
        if st.button(btn_label, key=f"save_{art_key}"):
            toggle_save({**article, "id": art_id})

        if link:
            st.markdown(f"[🌐 Ver noticia original]({link})")
