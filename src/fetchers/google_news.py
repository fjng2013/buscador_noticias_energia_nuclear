import urllib.parse
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional
import feedparser
from bs4 import BeautifulSoup
from src.config import load_sources_config


def clean_html(text: str) -> str:
    """Elimina etiquetas HTML residuales."""
    if not text:
        return ""
    soup = BeautifulSoup(text, "html.parser")
    return soup.get_text(separator=" ", strip=True)


def parse_entry_date(entry) -> Optional[str]:
    """Extrae la fecha en formato YYYY-MM-DD de una entrada RSS."""
    if hasattr(entry, "published_parsed") and entry.published_parsed:
        try:
            dt = datetime(*entry.published_parsed[:6])
            return dt.strftime("%Y-%m-%d")
        except Exception:
            pass
    if hasattr(entry, "updated_parsed") and entry.updated_parsed:
        try:
            dt = datetime(*entry.updated_parsed[:6])
            return dt.strftime("%Y-%m-%d")
        except Exception:
            pass
    return None


def fetch_google_news(target_date: Optional[date] = None) -> List[Dict]:
    """
    Recopila noticias de Google News RSS para España e Internacional.
    Si se especifica target_date, filtra las noticias correspondientes a esa fecha.
    """
    sources_cfg = load_sources_config().get("google_news", {})
    results = []

    target_date_str = target_date.strftime("%Y-%m-%d") if target_date else None

    # Configuración de ámbitos
    scopes = [
        ("Nacional", sources_cfg.get("national", {
            "query": "\"energía nuclear\" OR \"central nuclear\" OR \"Almaraz\" OR \"Vandellós\" OR \"Trillo\" OR \"Cofrentes\" OR \"Ascó\"",
            "language": "es",
            "country": "ES"
        })),
        ("Internacional", sources_cfg.get("international", {
            "query": "(\"nuclear energy\" OR \"nuclear power\" OR \"SMR\" OR \"small modular reactor\") -weapon",
            "language": "en",
            "country": "US"
        }))
    ]

    for scope_name, cfg in scopes:
        base_query = cfg.get("query", "nuclear energy")
        lang = cfg.get("language", "es")
        country = cfg.get("country", "ES")

        query = base_query
        # Si se especifica fecha, afinamos el término de búsqueda para Google News
        if target_date:
            next_day = target_date + timedelta(days=1)
            query += f" after:{target_date.strftime('%Y-%m-%d')} before:{next_day.strftime('%Y-%m-%d')}"

        encoded_query = urllib.parse.quote(query)
        rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl={lang}&gl={country}&ceid={country}:{lang}"

        try:
            feed = feedparser.parse(rss_url)
            for entry in feed.entries:
                entry_date = parse_entry_date(entry)

                # Si el usuario eligió una fecha y podemos parsear la fecha, verificamos coincidencia
                if target_date_str and entry_date and entry_date != target_date_str:
                    continue

                source_title = getattr(entry, "source", {}).get("title", "")
                if not source_title and "-" in entry.title:
                    source_title = entry.title.rsplit("-", 1)[-1].strip()

                clean_title = entry.title.rsplit("-", 1)[0].strip() if "-" in entry.title else entry.title
                summary = clean_html(getattr(entry, "summary", ""))

                results.append({
                    "title": clean_title,
                    "link": entry.link,
                    "date": entry_date or (target_date_str if target_date_str else datetime.utcnow().strftime("%Y-%m-%d")),
                    "media": source_title or "Google News",
                    "scope": scope_name,
                    "raw_summary": summary,
                    "origin": "Google News RSS"
                })
        except Exception as e:
            print(f"Error consultando Google News ({scope_name}): {e}")

    return results
