from datetime import date, datetime
from typing import List, Dict, Optional
from src.config import load_sources_config

try:
    from duckduckgo_search import DDGS
except ImportError:
    DDGS = None


def fetch_duckduckgo_news(target_date: Optional[date] = None, max_results: int = 15) -> List[Dict]:
    """
    Busca noticias sobre energía nuclear comercial mediante DuckDuckGo News.
    """
    if DDGS is None:
        return []

    sources_cfg = load_sources_config().get("duckduckgo", {})
    national_queries = sources_cfg.get("national_keywords", ["energia nuclear comercial España"])
    international_queries = sources_cfg.get("international_keywords", ["commercial nuclear power plant SMR"])

    results = []
    target_date_str = target_date.strftime("%Y-%m-%d") if target_date else None

    with DDGS() as ddgs:
        # Búsqueda Nacional
        for q in national_queries[:2]:
            try:
                search_query = f"{q} {target_date_str}" if target_date_str else q
                news_items = list(ddgs.news(keywords=search_query, region="es-es", max_results=max_results))
                for item in news_items:
                    item_date = item.get("date", "")
                    if item_date:
                        # Extraer solo la parte YYYY-MM-DD
                        item_date = item_date.split("T")[0]
                    if target_date_str and item_date and item_date != target_date_str:
                        continue

                    results.append({
                        "title": item.get("title", ""),
                        "link": item.get("url", ""),
                        "date": item_date or (target_date_str or datetime.utcnow().strftime("%Y-%m-%d")),
                        "media": item.get("source", "DuckDuckGo News"),
                        "scope": "Nacional",
                        "raw_summary": item.get("body", ""),
                        "origin": "DuckDuckGo"
                    })
            except Exception as e:
                print(f"Error en DuckDuckGo (Nacional - {q}): {e}")

        # Búsqueda Internacional
        for q in international_queries[:2]:
            try:
                search_query = f"{q} {target_date_str}" if target_date_str else q
                news_items = list(ddgs.news(keywords=search_query, region="wt-wt", max_results=max_results))
                for item in news_items:
                    item_date = item.get("date", "")
                    if item_date:
                        item_date = item_date.split("T")[0]
                    if target_date_str and item_date and item_date != target_date_str:
                        continue

                    results.append({
                        "title": item.get("title", ""),
                        "link": item.get("url", ""),
                        "date": item_date or (target_date_str or datetime.utcnow().strftime("%Y-%m-%d")),
                        "media": item.get("source", "DuckDuckGo News"),
                        "scope": "Internacional",
                        "raw_summary": item.get("body", ""),
                        "origin": "DuckDuckGo"
                    })
            except Exception as e:
                print(f"Error en DuckDuckGo (Internacional - {q}): {e}")

    return results
