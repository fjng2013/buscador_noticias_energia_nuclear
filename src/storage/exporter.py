import json
from datetime import date, datetime
from pathlib import Path
from typing import List, Dict, Optional
from src.config import RAW_DATA_DIR, PROCESSED_DATA_DIR, REPORTS_DIR


def save_raw_news(news_list: List[Dict], target_date: Optional[date] = None) -> Path:
    """Guarda las noticias recopiladas en bruto en data/raw/."""
    date_str = (target_date or date.today()).strftime("%Y-%m-%d")
    file_path = RAW_DATA_DIR / f"news_raw_{date_str}.json"

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(news_list, f, ensure_ascii=False, indent=2)

    return file_path


def save_processed_news(news_list: List[Dict], target_date: Optional[date] = None) -> Path:
    """Guarda las noticias analizadas y curadas en data/processed/."""
    date_str = (target_date or date.today()).strftime("%Y-%m-%d")
    file_path = PROCESSED_DATA_DIR / f"news_processed_{date_str}.json"

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(news_list, f, ensure_ascii=False, indent=2)

    return file_path


def load_processed_news_by_date(target_date: date) -> List[Dict]:
    """Carga noticias procesadas para una fecha específica si ya existen en disco."""
    date_str = target_date.strftime("%Y-%m-%d")
    file_path = PROCESSED_DATA_DIR / f"news_processed_{date_str}.json"

    if file_path.exists():
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []


def generate_markdown_report(news_list: List[Dict], target_date: Optional[date] = None) -> Path:
    """
    Genera un informe ejecutivo en formato Markdown en reports/
    con la tabla requerida: Link, Breve Resumen, Fecha y Medio.
    """
    date_str = (target_date or date.today()).strftime("%Y-%m-%d")
    file_path = REPORTS_DIR / f"informe_nuclear_{date_str}.md"

    national_news = [n for n in news_list if n.get("scope") == "Nacional"]
    intl_news = [n for n in news_list if n.get("scope") != "Nacional"]

    md_lines = [
        f"# ⚛️ Informe Ejecutivo de Noticias: Energía Nuclear Comercial",
        f"**Fecha del informe:** {date_str}  ",
        f"**Total de noticias analizadas:** {len(news_list)} (Nacional: {len(national_news)}, Internacional: {len(intl_news)})\n",
        "---\n",
        "## 🇪🇸 Ámbito Nacional (España)\n"
    ]

    if national_news:
        md_lines.append("| Medio | Fecha | Breve Resumen | Enlace a la Noticia |")
        md_lines.append("| :--- | :--- | :--- | :--- |")
        for item in national_news:
            media = item.get("media", "N/A").replace("|", "-")
            dt = item.get("date", date_str)
            summary = item.get("short_summary", "").replace("|", "-").replace("\n", " ")
            link = item.get("link", "#")
            title = item.get("title", "Ver noticia").replace("|", "-")
            md_lines.append(f"| **{media}** | {dt} | {summary} | [{title}]({link}) |")
    else:
        md_lines.append("_No se registraron noticias comerciales específicas para España en esta fecha._\n")

    md_lines.append("\n---\n")
    md_lines.append("## 🌍 Ámbito Internacional\n")

    if intl_news:
        md_lines.append("| Medio | Fecha | Breve Resumen | Enlace a la Noticia |")
        md_lines.append("| :--- | :--- | :--- | :--- |")
        for item in intl_news:
            media = item.get("media", "N/A").replace("|", "-")
            dt = item.get("date", date_str)
            summary = item.get("short_summary", "").replace("|", "-").replace("\n", " ")
            link = item.get("link", "#")
            title = item.get("title", "Ver noticia").replace("|", "-")
            md_lines.append(f"| **{media}** | {dt} | {summary} | [{title}]({link}) |")
    else:
        md_lines.append("_No se registraron noticias internacionales en esta fecha._\n")

    md_lines.append("\n---\n")
    md_lines.append(f"*Informe generado automáticamente por el Agente de Inteligencia de Energía Nuclear el {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}.*")

    with open(file_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))

    return file_path
