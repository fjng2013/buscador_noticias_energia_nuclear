import json
import logging
from datetime import date, datetime
from typing import List, Dict, Optional, Any
from config.prompts import ANALYSIS_SYSTEM_PROMPT, INVESTIGATION_RESEARCH_PROMPT
from src.agent.gemini_client import GeminiClient

logger = logging.getLogger(__name__)


def deduplicate_news(items: List[Dict]) -> List[Dict]:
    """Elimina noticias duplicadas basadas en URL o títulos muy similares."""
    seen_urls = set()
    seen_titles = set()
    unique = []

    for item in items:
        link = item.get("link", "").strip()
        title = item.get("title", "").strip().lower()

        # Normalizar título básico
        norm_title = "".join(ch for ch in title if ch.isalnum() or ch.isspace())

        if link and link in seen_urls:
            continue
        if norm_title and norm_title in seen_titles:
            continue

        if link:
            seen_urls.add(link)
        if norm_title:
            seen_titles.add(norm_title)
        unique.append(item)

    return unique


class NuclearNewsAnalyzer:
    """Agente de análisis y filtrado de noticias de energía nuclear comercial."""

    def __init__(self, gemini_client: Optional[GeminiClient] = None):
        self.gemini = gemini_client or GeminiClient()

    def analyze_news_batch(self, raw_items: List[Dict], target_date: Optional[date] = None) -> List[Dict]:
        """
        Filtra y analiza un conjunto de noticias mediante Gemini para asegurar
        que sean de energía nuclear comercial y genera los campos requeridos:
        link, short_summary, date, media, scope, topic.
        """
        deduped = deduplicate_news(raw_items)
        if not deduped:
            return []

        # Si Gemini está disponible, usamos el modelo para análisis de investigación
        if self.gemini.is_configured():
            return self._analyze_with_gemini(deduped, target_date)
        else:
            logger.info("Gemini no configurado. Usando filtrado heurístico de respaldo.")
            return self._heuristic_fallback(deduped, target_date)

    def _analyze_with_gemini(self, items: List[Dict], target_date: Optional[date] = None) -> List[Dict]:
        """Analiza noticias en lotes utilizando Gemini."""
        processed_results = []
        batch_size = 10  # Tamaño de lote óptimo para precisión y cuota

        target_date_str = target_date.strftime("%Y-%m-%d") if target_date else None

        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            prompt_data = [
                {
                    "id": idx,
                    "title": item.get("title"),
                    "link": item.get("link"),
                    "raw_summary": item.get("raw_summary"),
                    "media": item.get("media"),
                    "scope": item.get("scope"),
                    "date": item.get("date")
                }
                for idx, item in enumerate(batch)
            ]

            prompt = f"""Analiza las siguientes noticias para determinar si corresponden a ENERGÍA NUCLEAR COMERCIAL/CIVIL.
Descarta noticias militares o de armas nucleares.
Fecha objetivo solicitada (si aplica): {target_date_str or 'Cualquiera'}

Datos a analizar:
{json.dumps(prompt_data, ensure_ascii=False, indent=2)}

Devuelve una lista JSON con los objetos que SÍ sean de energía nuclear comercial.
Cada objeto DEBE incluir exactamente:
- "link": string (URL original de la noticia)
- "short_summary": string (Breve resumen en español, 2-3 frases explicando el hecho clave)
- "date": string (Fecha en formato YYYY-MM-DD)
- "media": string (Nombre del medio de comunicación o fuente)
- "title": string (Título claro en español)
- "scope": string ('Nacional' si es de España, 'Internacional' si es de otros países)
- "topic": string (Categoría: 'Regulación', 'SMR e Innovación', 'Operación y Vida Útil', 'Mercado y Economía', o 'Seguridad')
"""

            response_json = self.gemini.generate_json_response(
                prompt=prompt,
                system_instruction=ANALYSIS_SYSTEM_PROMPT
            )

            if response_json and isinstance(response_json, list):
                for res in response_json:
                    if isinstance(res, dict) and res.get("link"):
                        processed_results.append(res)
            else:
                # Si falló la llamada a Gemini para este lote, usamos fallback
                fallback_batch = self._heuristic_fallback(batch, target_date)
                processed_results.extend(fallback_batch)

        return deduplicate_news(processed_results)

    def _heuristic_fallback(self, items: List[Dict], target_date: Optional[date] = None) -> List[Dict]:
        """Filtrado de respaldo basado en reglas cuando no hay API key de Gemini."""
        discard_words = [
            "bomba", "misil", "ojiva", "guerra", "armamento", "arsenal", "weapon", "warhead",
            "pelea", "herido", "heridos", "calle", "detenido", "detenidos", "robo", "accidente de tráfico",
            "futbol", "fútbol", "liga", "baloncesto"
        ]
        
        nuclear_anchors = ["nuclear", "reactor", "smr", "oiea", "iaea", "csn", "uranio", "fisión", "fision"]

        target_date_str = target_date.strftime("%Y-%m-%d") if target_date else None
        valid_items = []

        for item in items:
            text = f"{item.get('title', '')} {item.get('raw_summary', '')}".lower()

            # Descartar sucesos, peleas y temas militares
            if any(w in text for w in discard_words):
                continue

            # Exigir explícitamente término nuclear o tecnológico clave
            if not any(anchor in text for anchor in nuclear_anchors):
                continue

            item_date = item.get("date")
            if target_date_str and item_date and item_date != target_date_str:
                continue

            title = item.get("title", "")
            raw_summary = item.get("raw_summary", "")
            summary = raw_summary if (raw_summary and len(raw_summary) > 20) else title

            valid_items.append({
                "title": title,
                "link": item.get("link", ""),
                "short_summary": summary[:250] + ("..." if len(summary) > 250 else ""),
                "date": item_date or (target_date_str or datetime.utcnow().strftime("%Y-%m-%d")),
                "media": item.get("media", "Medio Informativo"),
                "scope": item.get("scope", "Internacional"),
                "topic": "Energía Nuclear Comercial"
            })

        return valid_items

    def research_date(self, target_date: date) -> List[Dict]:
        """
        Investigación directa con Gemini 2.5 Pro sobre un día específico.
        """
        if not self.gemini.is_configured():
            return []

        prompt = INVESTIGATION_RESEARCH_PROMPT.format(target_date=target_date.strftime("%Y-%m-%d"))
        results = self.gemini.research_with_search_grounding(prompt, system_instruction=ANALYSIS_SYSTEM_PROMPT)
        if results and isinstance(results, list):
            return deduplicate_news(results)
        return []
