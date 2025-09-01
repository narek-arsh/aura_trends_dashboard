import os
import json
from typing import List, Dict

DATA_DIR = "data"
SAVED_PATH = os.path.join(DATA_DIR, "saved.json")

os.makedirs(DATA_DIR, exist_ok=True)

def _read_json(path, default):
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return default

def _save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_saved() -> List[Dict]:
    data = _read_json(SAVED_PATH, default=[])
    return data if isinstance(data, list) else []

def is_saved(art_id: str) -> bool:
    for a in get_saved():
        if a.get("id") == art_id:
            return True
    return False

def toggle_save(article: Dict) -> bool:
    """
    Alterna guardado. Devuelve True si queda guardado tras la operación,
    False si se elimina de guardados.
    """
    saved = get_saved()
    idx = next((i for i, a in enumerate(saved) if a.get("id") == article.get("id")), None)
    if idx is None:
        saved.append(article)
        _save_json(SAVED_PATH, saved)
        return True
    else:
        saved.pop(idx)
        _save_json(SAVED_PATH, saved)
        return False
