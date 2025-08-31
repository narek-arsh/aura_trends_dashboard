import google.generativeai as genai
import os

def configure_gemini():
    api_key = os.getenv("GEMINI_API_KEY")
    genai.configure(api_key=api_key)
    return genai.GenerativeModel("gemini-1.5-flash-latest")
