"""
Punto de entrada principal para despliegues en la nube:
Streamlit Community Cloud, Hugging Face Spaces, Render, Koyeb.
"""
import sys
from pathlib import Path

# Asegurar path raíz del proyecto
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Ejecutar la aplicación interactiva de Streamlit
import src.web.app
