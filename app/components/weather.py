import time
import streamlit as st

def render_weather():
    bust = int(time.time())
    st.markdown(
        f"""
        <iframe src="https://<tu-usuario>.github.io/malaga-weather-widget/?v={bust}"
                style="width:100%;height:200px;border:0;overflow:hidden;"
                loading="lazy"></iframe>
        """,
        unsafe_allow_html=True,
    )
