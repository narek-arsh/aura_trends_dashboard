import streamlit as st

def render_weather():
    st.markdown("""
<iframe src="https://narek-arsh.github.io/malaga-weather-widget/" width="100%" height="80" frameborder="0" scrolling="no"></iframe>
""", unsafe_allow_html=True)
# Widget del clima
