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
Eres un curador de contenido para un hotel 5* lifestyle de la marca ME by Meliá. 
Tu misión es detectar si la siguiente noticia es útil para un Aura Host.

Noticia:
Título: {article["title"]}
Resumen: {article["summary"]}

Responde en formato JSON válido:
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
