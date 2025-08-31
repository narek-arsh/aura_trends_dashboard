import google.generativeai as genai
import os
import json
import time

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")

def is_relevant_for_aura(article):
    prompt = f"""
Eres un experto en lujo, hospitalidad de alto nivel y tendencias internacionales. Evalúa si esta noticia es útil para un Aura Host de un hotel ME by Meliá, cuya misión es conocer lo último en moda, arte, gastronomía, música, bienestar y eventos relevantes. 

NOTICIA:
Título: {article['title']}
Resumen: {article.get('summary', 'Sin resumen disponible')}

RESPONDE SOLO EN FORMATO JSON:
{{
  "relevante": true/false,
  "motivo": "Breve frase explicando por qué sí o por qué no",
  "resumen": "Resumen con lo esencial",
  "idea_activacion": "Cómo se puede usar o mencionar esta noticia con un huésped ME"
}}
"""

    try:
        response = model.generate_content(prompt)
        time.sleep(5)  # ✅ Espera entre peticiones para no agotar el límite gratuito

        raw_text = response.text.strip()

        # Intentar parsear el JSON generado por la IA
        result = json.loads(raw_text)

        return {
            "relevante": result.get("relevante", False),
            "motivo": result.get("motivo", ""),
            "resumen": result.get("resumen", ""),
            "idea_activacion": result.get("idea_activacion", "")
        }

    except Exception as e:
        print(f"[!] Error al parsear respuesta IA: {e}")
        return {
            "relevante": False,
            "motivo": "Error de IA",
            "resumen": "",
            "idea_activacion": ""
        }
