from datetime import date, datetime
from typing import List, Dict, Optional
import requests
from src.config import NEWSAPI_KEY


def fetch_news_api(target_date: Optional[date] = None) -> List[Dict]:
    """
    Recopila noticias usando NewsAPI.org si NEWSAPI_KEY está configurada en .env.
    """
    if not NEWSAPI_KEY:
        return []

    target_date_str = target_date.strftime("%Y-%m-%d") if target_date else None
    results = []

    # Búsqueda Nacional e Internacional
    queries = [
        ("Nacional", "energia nuclear España OR Almaraz OR Vandellos OR Trillo OR Cofrentes OR Asco", "es"),
        ("Internacional", "\"nuclear energy\" OR \"nuclear power\" OR SMR -weapon", "en")
    ]

    for scope, q, lang in queries:
        url = "https://newsapi.org/v2/everything"
        params = {
            "q": q,
            "language": lang,
            "sortBy": "publishedAt",
            "pageSize": 20,
            "apiKey": NEWSAPI_KEY
        }
        if target_date_str:
            params["from"] = target_date_str
            params["to"] = target_date_str

        try:
            resp = requests.get(url, params=params, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                for art in data.get("articles", []):
                    pub_date = art.get("publishedAt", "")
                    if pub_date:
                        pub_date = pub_date.split("T")[0]

                    results.append({
                        "title": art.get("title", ""),
                        "link": art.get("url", ""),
                        "date": pub_date or (target_date_str or datetime.utcnow().strftime("%Y-%m-%d")),
                        "media": art.get("source", {}).get("name", "NewsAPI"),
                        "scope": scope,
                        "raw_summary": art.get("description", "") or art.get("title", ""),
                        "origin": "NewsAPI"
                    })
        except Exception as e:
            print(f"Error consultando NewsAPI ({scope}): {e}")

    return results
