import google.generativeai as genai
import os
import json

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def is_relevant_for_aura(article):
    prompt = f"""
Eres un curador de tendencias para el dashboard personal de un Aura Host del hotel ME by Meliá en Málaga.

Tu misión es detectar si una noticia trata sobre **tendencias actuales en moda, arte, cultura, gastronomía, bienestar o estilo de vida**, especialmente en el sector del lujo o el lifestyle experiencial.

Es relevante si:
- Habla de diseñadores, chefs, artistas, marcas, hoteles, restaurantes, galerías, exposiciones o eventos de alto nivel
- Trata sobre novedades, colecciones, aperturas, rankings, premios, colaboraciones, pop-ups, rituales de bienestar, experiencias sensoriales
- Tiene potencial para inspirar conversaciones o propuestas dentro del hotel ME
- Está relacionada con Málaga, Andalucía o el contexto europeo

Es irrelevante si:
- Es solo una noticia económica o de resultados financieros sin valor experiencial
- Es una reseña de producto sin contexto de lujo, diseño o creatividad
- Es un contenido político, policial o ajeno al mundo de tendencias o experiencias

Aquí tienes la noticia:

Título: {article["title"]}
Resumen: {article["summary"]}

Responde solo con un JSON válido:
{{
  "es_util": true/false,
  "why_it_matters": "...",
  "ideas_activacion": "..."
}}
    """.strip()

    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(prompt)

    try:
        return json.loads(response.text)
    except Exception as e:
        print(f"[!] Error al parsear respuesta IA: {e}")
        return {"es_util": False, "why_it_matters": "", "ideas_activacion": ""}
# Lógica de filtrado e IA con Gemini
