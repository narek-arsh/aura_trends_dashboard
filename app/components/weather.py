import streamlit as st

def render_weather():
    """Widget del tiempo para Málaga (iframe)."""
    st.markdown(
        """
        <iframe src="https://narek-arsh.github.io/malaga-weather-widget/"
                style="width:100%; height:140px; border:0; border-radius:12px; overflow:hidden;"
                loading="lazy"></iframe>
        """,
        unsafe_allow_html=True,
    )

# Alias por compatibilidad con versiones anteriores
def render_weather_widget():
    return render_weather()
