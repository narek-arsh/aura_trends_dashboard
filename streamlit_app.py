import streamlit as st
from app.pages.Radar import main as radar_main

st.set_page_config(page_title="Aura Trends", layout="wide")
radar_main()
