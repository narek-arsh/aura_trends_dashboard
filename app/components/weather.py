import time
import streamlit as st

def render_weather():
    # Cache buster → cambia cada ejecución para forzar refresco
    bust = int(time.time())
    st.markdown(
        f"""
        <iframe src="https://<tu-usuario>.github.io/malaga-weather-widget/?v={bust}"
                style="width:100%;height:240px;border:0;border-radius:12px;overflow:hidden;"
                loading="lazy"></iframe>
        """,
        unsafe_allow_html=True,
    )
