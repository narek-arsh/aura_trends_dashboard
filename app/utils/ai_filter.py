import os
import time
import google.generativeai as genai

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")

def is_relevant_for_aura(article):
    """
    Devuelve True/False. Pausa 5s por llamada para no superar cuota.
    """
    prompt = f"""
Eres curador de tendencias para un hotel de lujo lifestyle (ME by Meliá, Málaga).
¿Esta noticia puede servir para conversación/experiencia (moda, arte, gastronomía, lifestyle, bienestar, eventos, lujo, cultura)?

Responde SOLO con: true  o  false

Título: {article.get('title','')}
Resumen: {article.get('summary','')}
Categoría: {article.get('category','')}
Enlace: {article.get('link','')}
""".strip()

    try:
        resp = model.generate_content(prompt)
        text = (resp.text or "").strip().lower()
    except Exception as e:
        print(f"[IA] Error al generar contenido: {e}")
        # Fallback conservador: lo marcamos como NO relevante
        return False
    finally:
        time.sleep(5)  # anti rate-limit

    if "true" in text:
        return True
    if "false" in text:
        return False

    # Si la salida no es clara, mejor ser conservador para no llenar ruido
    print(f"[IA] Respuesta inesperada: {text!r}")
    return False
