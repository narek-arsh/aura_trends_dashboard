import google.generativeai as genai
import os
import json

# Cargar clave desde variable de entorno (usada en GitHub Actions)
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel("models/gemini-1.5-flash")

def is_relevant_for_aura(article):
    """
    Llama a Gemini y pregunta si esta noticia es útil para un Aura Host.
    Si sí, también genera resumen, why it matters, y activaciones.
    """
    prompt = f"""
Eres un curador de tendencias para el dashboard personal de un Aura Host del hotel ME by Meliá en Málaga.

Tu misión es detectar si una noticia trata sobre **tendencias actuales en moda, arte, cultura, gastronomía, bienestar o estilo de vida**, especialmente en el sector del lujo o el lifestyle experiencial.

Es relevante si:
- Habla de diseñadores, chefs, artistas, marcas, hoteles, restaurantes, galerías, exposiciones o eventos de alto nivel
- Trata sobre novedades, colecciones, aperturas, rankings, premios, colaboraciones, pop-ups, rituales de bienestar, experiencias sensoriales
- Tiene potencial para inspirar conversaciones o propuestas dentro del hotel ME (por ejemplo, sugerir una exposición, explicar una tendencia, recomendar una marca o una experiencia local)
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


    try:
        response = model.generate_content(prompt)
        raw = response.text.strip()

        # Intentar parsear como JSON
        result = json.loads(raw)

        if result.get("es_util") is True:
            return {
                "why_it_matters": result.get("why_it_matters", "").strip(),
                "ideas_activacion": result.get("ideas_activacion", "").strip(),
            }
        else:
            return None

    except Exception as e:
        print(f"[AI FILTER] Error al procesar con Gemini: {e}")
        return None
