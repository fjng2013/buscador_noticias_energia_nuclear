from datetime import date, datetime
from typing import List, Dict, Optional
import feedparser
import requests
from bs4 import BeautifulSoup
from src.config import load_sources_config


def clean_html(text: str) -> str:
    """Elimina etiquetas HTML."""
    if not text:
        return ""
    soup = BeautifulSoup(text, "html.parser")
    return soup.get_text(separator=" ", strip=True)


def parse_date(entry) -> Optional[str]:
    """Obtiene la fecha YYYY-MM-DD del feed."""
    if hasattr(entry, "published_parsed") and entry.published_parsed:
        try:
            return datetime(*entry.published_parsed[:6]).strftime("%Y-%m-%d")
        except Exception:
            pass
    if hasattr(entry, "updated_parsed") and entry.updated_parsed:
        try:
            return datetime(*entry.updated_parsed[:6]).strftime("%Y-%m-%d")
        except Exception:
            pass
    return None


def fetch_official_sources(target_date: Optional[date] = None) -> List[Dict]:
    """
    Recopila noticias de fuentes oficiales y especializadas:
    CSN, Foro Nuclear, World Nuclear News (WNN), OIEA/IAEA.
    """
    sources_cfg = load_sources_config().get("official_sources", [])
    results = []
    target_date_str = target_date.strftime("%Y-%m-%d") if target_date else None

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    for src in sources_cfg:
        name = src.get("name", "Organismo Oficial")
        scope = "Nacional" if src.get("scope") == "national" else "Internacional"
        src_type = src.get("type", "rss")
        url = src.get("url")

        if not url:
            continue

        try:
            if src_type == "rss":
                # Descargar con requests y parsear feed
                resp = requests.get(url, headers=headers, timeout=10)
                if resp.status_code == 200:
                    feed = feedparser.parse(resp.content)
                    for entry in feed.entries[:20]:
                        entry_date = parse_date(entry)
                        if target_date_str and entry_date and entry_date != target_date_str:
                            continue

                        results.append({
                            "title": entry.title.strip(),
                            "link": entry.link,
                            "date": entry_date or (target_date_str or datetime.utcnow().strftime("%Y-%m-%d")),
                            "media": name,
                            "scope": scope,
                            "raw_summary": clean_html(getattr(entry, "summary", "")),
                            "origin": "Organismo Oficial"
                        })

            elif src_type == "web_scrape":
                # Scraping de apoyo para Foro Nuclear
                resp = requests.get(url, headers=headers, timeout=10)
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, "html.parser")
                    # Buscar artículos en la página de Foro Nuclear
                    articles = soup.find_all("article") or soup.find_all("div", class_="post")
                    for art in articles[:10]:
                        a_tag = art.find("a")
                        title_tag = art.find(["h2", "h3", "h4"])
                        if not a_tag or not title_tag:
                            continue

                        link = a_tag.get("href", "")
                        title = title_tag.get_text(strip=True)
                        time_tag = art.find("time")
                        art_date = time_tag.get_text(strip=True) if time_tag else None

                        if target_date_str and art_date and target_date_str not in art_date:
                            continue

                        results.append({
                            "title": title,
                            "link": link,
                            "date": target_date_str or datetime.utcnow().strftime("%Y-%m-%d"),
                            "media": name,
                            "scope": scope,
                            "raw_summary": title,
                            "origin": "Organismo Oficial"
                        })

        except Exception as e:
            print(f"Error consultando fuente oficial {name}: {e}")

    return results
