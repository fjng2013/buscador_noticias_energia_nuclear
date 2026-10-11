import json
import os
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# Claves de API (compatibles con .env local y con st.secrets en despliegues en la nube)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY", "").strip()

try:
    import streamlit as st
    if hasattr(st, "secrets"):
        if "GEMINI_API_KEY" in st.secrets and not GEMINI_API_KEY:
            GEMINI_API_KEY = str(st.secrets["GEMINI_API_KEY"]).strip()
        if "GEMINI_MODEL" in st.secrets and (not GEMINI_MODEL or GEMINI_MODEL == "gemini-2.5-flash"):
            GEMINI_MODEL = str(st.secrets["GEMINI_MODEL"]).strip()
        if "NEWSAPI_KEY" in st.secrets and not NEWSAPI_KEY:
            NEWSAPI_KEY = str(st.secrets["NEWSAPI_KEY"]).strip()
except Exception:
    pass

# Directorios de datos y reportes
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
REPORTS_DIR = BASE_DIR / "reports"
CONFIG_DIR = BASE_DIR / "config"

# Asegurar existencia de directorios
RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# Cargar configuración de fuentes
SOURCES_CONFIG_PATH = CONFIG_DIR / "sources.json"


def load_sources_config() -> dict:
    """Carga el archivo sources.json con las fuentes de noticias."""
    if SOURCES_CONFIG_PATH.exists():
        with open(SOURCES_CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}
