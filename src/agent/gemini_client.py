import json
import logging
from typing import Optional, List, Dict, Any
from src.config import GEMINI_API_KEY, GEMINI_MODEL

logger = logging.getLogger(__name__)


class GeminiClient:
    """Cliente para interactuar con la API de Google Gemini."""

    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        self.api_key = api_key or GEMINI_API_KEY
        self.model_name = model_name or GEMINI_MODEL or "gemini-2.5-pro"
        self.client = None
        self._init_client()

    def _init_client(self):
        if not self.api_key or self.api_key == "tu_api_key_de_gemini_aqui":
            logger.warning("No se ha configurado una GEMINI_API_KEY válida.")
            return

        try:
            # Intentar primero con el SDK oficial más moderno google-genai
            from google import genai
            self.client = genai.Client(api_key=self.api_key)
            self.sdk_type = "google-genai"
        except ImportError:
            try:
                # Fallback a google-generativeai clásico
                import google.generativeai as legacy_genai
                legacy_genai.configure(api_key=self.api_key)
                self.client = legacy_genai.GenerativeModel(self.model_name)
                self.sdk_type = "google-generativeai"
            except ImportError:
                logger.error("No se encontró ningún SDK de Google Gemini instalado.")
                self.client = None
                self.sdk_type = None

    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_key != "tu_api_key_de_gemini_aqui" and self.client)

    def generate_json_response(self, prompt: str, system_instruction: Optional[str] = None) -> Optional[Any]:
        """
        Ejecuta una consulta a Gemini esperando una respuesta estructurada en JSON.
        """
        if not self.is_configured():
            logger.warning("GeminiClient no está configurado con una API key válida.")
            return None

        try:
            if self.sdk_type == "google-genai":
                from google.genai import types

                config = types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    response_mime_type="application/json",
                    temperature=0.2,
                )
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config=config
                )
                text = response.text.strip()
                return json.loads(text)

            elif self.sdk_type == "google-generativeai":
                import google.generativeai as legacy_genai
                model = legacy_genai.GenerativeModel(
                    self.model_name,
                    system_instruction=system_instruction,
                    generation_config={"response_mime_type": "application/json", "temperature": 0.2}
                )
                response = model.generate_content(prompt)
                text = response.text.strip()
                return json.loads(text)

        except Exception as e:
            logger.error(f"Error generando respuesta con Gemini ({self.model_name}): {e}")
            # Intentar limpiar delimitadores markdown ```json ... ``` si falló json.loads
            try:
                if 'response' in locals() and hasattr(response, 'text'):
                    cleaned = response.text.strip()
                    if cleaned.startswith("```json"):
                        cleaned = cleaned[7:]
                    if cleaned.startswith("```"):
                        cleaned = cleaned[3:]
                    if cleaned.endswith("```"):
                        cleaned = cleaned[:-3]
                    return json.loads(cleaned.strip())
            except Exception:
                pass
            return None

    def research_with_search_grounding(self, prompt: str, system_instruction: Optional[str] = None) -> Optional[Any]:
        """
        Investiga noticias en tiempo real con Google Search Grounding activado en Gemini.
        """
        if not self.is_configured():
            return None

        try:
            if self.sdk_type == "google-genai":
                from google.genai import types

                config = types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    tools=[types.Tool(google_search=types.GoogleSearch())],
                    temperature=0.2,
                )
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt + "\n\nResponde estrictamente con un array JSON de noticias con formato:\n[{\"title\": \"...\", \"link\": \"...\", \"short_summary\": \"...\", \"date\": \"YYYY-MM-DD\", \"media\": \"...\", \"scope\": \"Nacional|Internacional\", \"topic\": \"...\"}]",
                    config=config
                )
                text = response.text.strip()
                if "```json" in text:
                    text = text.split("```json")[1].split("```")[0].strip()
                elif "```" in text:
                    text = text.split("```")[1].split("```")[0].strip()
                return json.loads(text)
        except Exception as e:
            logger.warning(f"No se pudo usar Search Grounding directamente o falló el parsing: {e}")
            return None
