# ⚛️ Agente de Inteligencia de Noticias: Energía Nuclear Comercial

Agente inteligente autónomo diseñado para buscar, filtrar y resumir noticias sobre **energía nuclear civil y comercial**, tanto a nivel **Nacional (España)** como a nivel **Internacional**.

El agente utiliza las capacidades de razonamiento profundo del modelo **Gemini 2.5 Pro** de Google (mediante la API gratuita de Google AI Studio) para descartar contenidos militares/bélicos y generar resúmenes ejecutivos precisos.

---

## 📁 Estructura del Proyecto

```text
buscador_noticias_energia_nuclear/
├── config/
│   ├── sources.json            # Configuración de consultas, fuentes oficiales y RSS
│   └── prompts.py              # Prompts especializados para filtrado y análisis con Gemini
├── data/
│   ├── raw/                    # Noticias en bruto recopiladas de las APIs/feeds (JSON)
│   └── processed/              # Noticias analizadas, curadas y clasificadas (JSON)
├── reports/                    # Informes ejecutivos periódicos en Markdown (.md)
├── src/
│   ├── config.py               # Gestión de variables de entorno y rutas
│   ├── fetchers/               # Recolectores de fuentes gratuitas
│   │   ├── google_news.py      # Google News RSS (España e Internacional)
│   │   ├── duckduckgo_news.py  # DuckDuckGo News
│   │   ├── official_sources.py # CSN, Foro Nuclear, World Nuclear News (WNN), OIEA/IAEA
│   │   └── news_api.py         # NewsAPI (opcional si se dispone de key)
│   ├── agent/                  # Agente de IA con Gemini
│   │   ├── gemini_client.py    # Cliente API para Gemini 2.5 Pro / Flash
│   │   └── analyzer.py         # Filtrado estricto comercial y resúmenes
│   ├── storage/                # Almacenamiento JSON y generador de tablas Markdown
│   │   └── exporter.py
│   ├── web/                    # Interfaz visual interactiva
│   │   └── app.py              # Panel Streamlit con selector de día, tabla y métricas
│   └── main.py                 # Orquestador del pipeline en CLI
├── .env.example                # Plantilla de variables de entorno
├── requirements.txt            # Dependencias de Python
└── README.md                   # Documentación paso a paso
```

---

## 🚀 Guía de Inicio Paso a Paso

### 1. Requisitos Previos
- Python 3.10 o superior instalado en el sistema.

### 2. Instalación de Dependencias
Abre una terminal en esta carpeta y ejecuta:

```powershell
pip install -r requirements.txt
```

*(Opcional recomendado: crear un entorno virtual con `python -m venv .venv` y activarlo antes de instalar).*

---

### 3. Configuración de la API Key Gratuita de Gemini

1. Obtén tu clave API gratuita en [Google AI Studio](https://aistudio.google.com/).
2. Copia el archivo `.env.example` como `.env`:
   ```powershell
   copy .env.example .env
   ```
3. Edita `.env` e introduce tu clave:
   ```env
   GEMINI_API_KEY=tu_clave_real_aqui
   GEMINI_MODEL=gemini-2.5-pro
   ```
   *(Nota: Si aún no tienes la clave, el sistema cuenta con un modo de respaldo heurístico y también te permite ingresar la clave directamente en la interfaz web).*

---

### 4. Ejecución de la Interfaz Web Interactiva

Para abrir el panel visual interactivo con selector de fecha y tabla de noticias:

```powershell
streamlit run src/web/app.py
```

Se abrirá automáticamente en tu navegador (`http://localhost:8501`). Desde allí podrás:
- **Elegir cualquier día** con el calendario selector.
- **Lanzar la investigación del agente** con un solo clic.
- **Filtrar por ámbito**: Todas, España (Nacional) o Internacional.
- **Buscar palabras clave** (ej. Almaraz, SMR, licencias, fusión, uranio).
- **Consultar la tabla interactiva** con: Medio, Fecha, Ámbito, Breve Resumen y Enlace directo a la noticia.
- **Descargar el informe ejecutivo** en formato `.md` (Markdown).

---

### 5. Ejecución por Línea de Comandos (CLI)

Si prefieres ejecutar el agente en segundo plano o mediante un script automatizado para una fecha concreta:

```powershell
# Ejecutar para el día de hoy
python src/main.py

# Ejecutar para un día específico
python src/main.py --date 2026-10-11
```

Esto generará automáticamente:
- `data/raw/news_raw_YYYY-MM-DD.json`
- `data/processed/news_processed_YYYY-MM-DD.json`
- `reports/informe_nuclear_YYYY-MM-DD.md`

---

## 💡 Modelo Seleccionado

Se ha predeterminado **Gemini 2.5 Pro** (`gemini-2.5-pro`) porque es el modelo más avanzado de Google para razonamiento complejo, investigación documental y síntesis periodística. Permite además grounding con búsqueda en Google para corroborar las fuentes y fechas de las noticias comerciales.
