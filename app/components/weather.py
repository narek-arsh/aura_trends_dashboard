import streamlit as st
from streamlit.components.v1 import html

def render_weather():
    """
    Widget del tiempo incrustado DIRECTO con components.html para evitar
    problemas de caché/iframe. Usa el ID que me diste (ww_be23d3638fe54).
    """
    html(
        """
        <!DOCTYPE html>
        <html lang="es">
        <head>
          <meta charset="utf-8" />
          <meta name="viewport" content="width=device-width,initial-scale=1" />
          <style>
            html, body { margin:0; padding:0; background:#f5f7fb; }
            #ww_be23d3638fe54 { display:block; min-height:220px; max-width:100%; }
          </style>
        </head>
        <body>
          <div id="ww_be23d3638fe54" v="1.3" loc="id"
               a='{"t":"responsive","lang":"es","sl_lpl":1,"ids":["wl4505"],
                   "font":"Arial","sl_ics":"one_a","sl_sot":"celsius",
                   "cl_bkg":"image","cl_font":"#FFFFFF","cl_cloud":"#FFFFFF",
                   "cl_persp":"#81D4FA","cl_sun":"#FFC107","cl_moon":"#FFC107",
                   "cl_thund":"#FF5722"}'>
            Más previsiones:
            <a href="https://oneweather.org/es/malaga/25_days/"
               id="ww_be23d3638fe54_u" target="_blank">Málaga tiempo 25 días</a>
          </div>
          <script async src="https://app3.weatherwidget.org/js/?id=ww_be23d3638fe54"></script>
          <noscript>Activa JavaScript para ver el widget del tiempo.</noscript>
        </body>
        </html>
        """,
        height=260,  # ajusta si ves recorte
        scrolling=False
    )

# Alias por compatibilidad
def render_weather_widget():
    return render_weather()
