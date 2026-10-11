import argparse
import sys
from datetime import datetime, date
from pathlib import Path

# Asegurar encoding UTF-8 en Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

# Asegurar path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.fetchers.google_news import fetch_google_news
from src.fetchers.duckduckgo_news import fetch_duckduckgo_news
from src.fetchers.official_sources import fetch_official_sources
from src.fetchers.news_api import fetch_news_api
from src.agent.analyzer import NuclearNewsAnalyzer
from src.storage.exporter import save_raw_news, save_processed_news, generate_markdown_report


def run_agent_pipeline(target_date: date) -> dict:
    """
    Ejecuta el pipeline completo del agente para la fecha seleccionada.
    """
    print(f"\n⚛️ Iniciando búsqueda e investigación para la fecha: {target_date.strftime('%Y-%m-%d')}...")

    # 1. Recopilación de fuentes
    print("📡 [1/4] Consultando Google News RSS...")
    gn_news = fetch_google_news(target_date)
    print(f"   -> Encontradas: {len(gn_news)} noticias")

    print("📡 [2/4] Consultando DuckDuckGo News...")
    ddg_news = fetch_duckduckgo_news(target_date)
    print(f"   -> Encontradas: {len(ddg_news)} noticias")

    print("📡 [3/4] Consultando fuentes oficiales y especializadas (CSN, Foro Nuclear, WNN, IAEA)...")
    official_news = fetch_official_sources(target_date)
    print(f"   -> Encontradas: {len(official_news)} noticias")

    print("📡 [4/4] Consultando NewsAPI (si configurado)...")
    api_news = fetch_news_api(target_date)
    print(f"   -> Encontradas: {len(api_news)} noticias")

    all_raw = gn_news + ddg_news + official_news + api_news
    print(f"📊 Total en bruto recolectado: {len(all_raw)} noticias")

    # Guardar raw data
    raw_path = save_raw_news(all_raw, target_date)

    # 2. Análisis y filtrado con el Agente Gemini
    print("🧠 Analizando, filtrando y resumiendo con el Agente Gemini (filtrado comercial exclusivo)...")
    analyzer = NuclearNewsAnalyzer()
    processed = analyzer.analyze_news_batch(all_raw, target_date)

    # 3. Guardar datos procesados
    proc_path = save_processed_news(processed, target_date)

    # 4. Generar informe Markdown con la tabla
    report_path = generate_markdown_report(processed, target_date)

    print(f"\n✅ Proceso completado:")
    print(f"   - Noticias procesadas válidas: {len(processed)}")
    print(f"   - Datos crudos guardados en: {raw_path}")
    print(f"   - Datos procesados en: {proc_path}")
    print(f"   - Informe Markdown generado en: {report_path}")

    return {
        "target_date": target_date.strftime("%Y-%m-%d"),
        "raw_count": len(all_raw),
        "processed_count": len(processed),
        "news": processed,
        "raw_path": str(raw_path),
        "processed_path": str(proc_path),
        "report_path": str(report_path)
    }


def main():
    parser = argparse.ArgumentParser(description="Agente de Noticias sobre Energía Nuclear Comercial")
    parser.add_argument(
        "--date",
        type=str,
        help="Fecha de las noticias en formato YYYY-MM-DD (por defecto hoy)",
        default=date.today().strftime("%Y-%m-%d")
    )
    args = parser.parse_args()

    try:
        target_date = datetime.strptime(args.date, "%Y-%m-%d").date()
    except ValueError:
        print(f"Formato de fecha inválido: {args.date}. Usa YYYY-MM-DD.")
        sys.exit(1)

    result = run_agent_pipeline(target_date)

    print("\n" + "=" * 80)
    print("TABLA DE NOTICIAS:")
    print("=" * 80)
    for n in result["news"]:
        print(f"[{n.get('scope', 'N/A')}] | {n.get('media', 'N/A')} | {n.get('date', 'N/A')}")
        print(f"Título: {n.get('title', '')}")
        print(f"Resumen: {n.get('short_summary', '')}")
        print(f"Enlace: {n.get('link', '')}")
        print("-" * 80)


if __name__ == "__main__":
    main()
