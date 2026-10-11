"""
Punto de entrada principal para despliegues en la nube:
Streamlit Community Cloud, Hugging Face Spaces, Render, Koyeb.
"""
import sys
import runpy
from pathlib import Path

# Asegurar path raíz del proyecto
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Ejecutar la aplicación interactiva en cada ciclo de Streamlit
app_file = BASE_DIR / "src" / "web" / "app.py"
runpy.run_path(str(app_file), run_name="__main__")
