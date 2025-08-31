import google.generativeai as genai
import os
import json

# ⚙️ Configurar la API de Gemini
api_key = os.getenv("GEMINI_API_KEY")
print("🧪 GEMINI_API_KEY presente:", bool(api_key))
genai.configure(api_key=api_key)

model = genai.GenerativeModel("gemini-1.5-flash")

# ✅ Evaluación de relevancia para el universo Aura
def is_relevant_for_aura(article):
    prompt = f"""
¿Este artículo podría interesar a un huésped de un hotel de lujo lifestyle como el ME by Meliá? Evalúa si aporta valor como experiencia, estilo, cultura, tendencia o curiosidad. 
Devuelve únicamente "true" si lo consideras relevante, o "false" si no lo es.

Título: {article.get('title', '')}
Resumen: {article.get('summary', '')}
Categoría: {article.get('category', '')}
Fuente: {article.get('link', '')}
    """.strip()

    try:
        response = model.generate_content(prompt)
        raw = response.text.strip().lower()

        # 🧠 Asegurar salida válida
        if "true" in raw:
            return True
        elif "false" in raw:
            return False
        else:
            raise ValueError(f"Respuesta inesperada: {raw}")

    except Exception as e:
        print(f"[!] Error al parsear respuesta IA: {e}")
        return False
