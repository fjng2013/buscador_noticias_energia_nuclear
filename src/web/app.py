import os
import sys
from datetime import date, datetime
from pathlib import Path
import pandas as pd
import streamlit as st

# Configurar path raíz del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

from src.config import GEMINI_API_KEY, GEMINI_MODEL
from src.agent.gemini_client import GeminiClient
from src.agent.analyzer import NuclearNewsAnalyzer
from src.fetchers.google_news import fetch_google_news
from src.fetchers.duckduckgo_news import fetch_duckduckgo_news
from src.fetchers.official_sources import fetch_official_sources
from src.fetchers.news_api import fetch_news_api
from src.storage.exporter import (
    save_raw_news,
    save_processed_news,
    load_processed_news_by_date,
    generate_markdown_report,
    REPORTS_DIR
)

# Configuración de página de Streamlit
st.set_page_config(
    page_title="Agente Nuclear | Inteligencia Comercial",
    page_icon="⚛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Título y encabezado principal (100% nativo de Streamlit, sin código HTML)
st.title("⚛️ Agente de Noticias: Energía Nuclear Comercial")
st.caption("Monitorización inteligente a nivel Nacional (España) e Internacional con filtrado exclusivo de energía civil y comercial.")

# ----------------- SIDEBAR: Parámetros y Configuración -----------------
with st.sidebar:
    st.header("⚙️ Configuración")

    # Selección de fecha
    st.subheader("📅 Fecha a Consultar")
    selected_date = st.date_input(
        "Elige el día de las noticias:",
        value=date.today(),
        max_value=date.today(),
        help="El agente buscará o cargará las noticias correspondientes a esta fecha."
    )

    st.markdown("---")

    # Selección del modelo Gemini
    st.subheader("🧠 Modelo de Gemini")
    model_choice = st.selectbox(
        "Modelo para investigación y filtrado:",
        options=["gemini-2.5-flash", "gemini-3-flash-preview", "gemini-2.5-pro"],
        index=0,
        help="gemini-2.5-flash ofrece excelente razonamiento, alta velocidad y disponibilidad directa con la cuota gratuita."
    )

    # API Key de Gemini
    st.subheader("🔑 Clave de Gemini")
    user_api_key = st.text_input(
        "GEMINI_API_KEY:",
        value=GEMINI_API_KEY if (GEMINI_API_KEY and GEMINI_API_KEY != "tu_api_key_de_gemini_aqui") else "",
        type="password",
        help="Tu clave gratuita de Google AI Studio. Si está en .env se carga automáticamente."
    )

    if user_api_key:
        st.success("API Key conectada", icon="✅")
    else:
        st.info("Introduce tu clave de Gemini para activar el filtrado inteligente.", icon="ℹ️")

    st.markdown("---")

    # Fuentes activas
    st.subheader("📡 Fuentes de Información")
    use_google_news = st.checkbox("Google News RSS", value=True)
    use_ddg = st.checkbox("DuckDuckGo News", value=True)
    use_officials = st.checkbox("Organismos (CSN, Foro, WNN, OIEA)", value=True)
    use_newsapi = st.checkbox("NewsAPI (si key disponible)", value=True)

    st.markdown("---")
    st.caption("Desarrollado con Python + Google Gemini + Streamlit")


# ----------------- LÓGICA DE BÚSQUEDA Y CARGA -----------------

cached_news = load_processed_news_by_date(selected_date)

col_actions, col_status = st.columns([1, 2])

with col_actions:
    run_search = st.button("🚀 Buscar e Investigar con el Agente", type="primary", use_container_width=True)

with col_status:
    if cached_news and not run_search:
        st.success(f"Hay **{len(cached_news)}** noticias guardadas para el día **{selected_date.strftime('%Y-%m-%d')}**.", icon="💾")
    elif not cached_news and not run_search:
        st.warning(f"No hay noticias guardadas aún para el **{selected_date.strftime('%Y-%m-%d')}**. Pulsa el botón para buscar.", icon="🔎")

news_to_display = cached_news

if run_search:
    with st.spinner(f"El Agente está buscando y analizando noticias de energía nuclear comercial para el {selected_date.strftime('%Y-%m-%d')}..."):
        all_raw = []

        if use_google_news:
            gn = fetch_google_news(selected_date)
            all_raw.extend(gn)

        if use_ddg:
            ddg = fetch_duckduckgo_news(selected_date)
            all_raw.extend(ddg)

        if use_officials:
            off = fetch_official_sources(selected_date)
            all_raw.extend(off)

        if use_newsapi:
            na = fetch_news_api(selected_date)
            all_raw.extend(na)

        save_raw_news(all_raw, selected_date)

        client = GeminiClient(api_key=user_api_key, model_name=model_choice)
        analyzer = NuclearNewsAnalyzer(gemini_client=client)

        processed = analyzer.analyze_news_batch(all_raw, selected_date)

        if client.is_configured() and len(processed) < 5:
            extra_research = analyzer.research_date(selected_date)
            if extra_research:
                processed.extend(extra_research)

        save_processed_news(processed, selected_date)
        generate_markdown_report(processed, selected_date)

        news_to_display = processed
        st.rerun()

# ----------------- VISUALIZACIÓN DE RESULTADOS -----------------

if news_to_display:
    total_count = len(news_to_display)
    nac_count = len([n for n in news_to_display if n.get("scope") == "Nacional"])
    int_count = total_count - nac_count

    # Métricas nativas de Streamlit
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Noticias", total_count)
    m2.metric("España (Nacional)", nac_count)
    m3.metric("Internacional", int_count)

    with m4:
        report_file = REPORTS_DIR / f"informe_nuclear_{selected_date.strftime('%Y-%m-%d')}.md"
        report_content = ""
        if report_file.exists():
            with open(report_file, "r", encoding="utf-8") as rf:
                report_content = rf.read()
        else:
            generate_markdown_report(news_to_display, selected_date)
            if report_file.exists():
                with open(report_file, "r", encoding="utf-8") as rf:
                    report_content = rf.read()

        st.download_button(
            label="📄 Descargar Informe .md",
            data=report_content,
            file_name=f"informe_nuclear_{selected_date.strftime('%Y-%m-%d')}.md",
            mime="text/markdown",
            use_container_width=True
        )

    st.divider()

    # Filtros y buscador
    f_col1, f_col2 = st.columns([1, 2])
    with f_col1:
        scope_filter = st.selectbox("Filtrar por Ámbito:", ["Todos", "Nacional (España)", "Internacional"])
    with f_col2:
        search_query = st.text_input("Buscar por palabra clave (ej. Almaraz, SMR, licencias, inversión):", "")

    # Aplicar filtros
    filtered = news_to_display
    if scope_filter == "Nacional (España)":
        filtered = [n for n in filtered if n.get("scope") == "Nacional"]
    elif scope_filter == "Internacional":
        filtered = [n for n in filtered if n.get("scope") != "Nacional"]

    if search_query:
        sq = search_query.lower()
        filtered = [
            n for n in filtered
            if sq in n.get("title", "").lower()
            or sq in n.get("short_summary", "").lower()
            or sq in n.get("media", "").lower()
        ]

    st.subheader(f"Noticias Disponibles ({len(filtered)})")

    if filtered:
        # Pestañas para elegir el modo de lectura preferido
        tab_cards, tab_table = st.tabs(["📰 Vista de Tarjetas (Fácil Lectura + Copia)", "📊 Vista de Tabla Interactiva"])

        # ----------------- PESTAÑA 1: VISTA DE TARJETAS -----------------
        with tab_cards:
            for idx, item in enumerate(filtered, start=1):
                with st.container(border=True):
                    scope = item.get("scope", "Internacional")
                    scope_badge = "🇪🇸 **Nacional (España)**" if scope == "Nacional" else "🌍 **Internacional**"
                    media = item.get("media", "Medio Informativo")
                    dt = item.get("date", selected_date.strftime("%Y-%m-%d"))
                    topic = item.get("topic", "Energía Nuclear Comercial")
                    title = item.get("title", "Noticia sin título")
                    summary = item.get("short_summary", "Sin resumen disponible")
                    link = item.get("link", "#")

                    # Fila superior de metadatos limpia
                    st.markdown(f"{scope_badge} &nbsp;|&nbsp; 🏢 **Medio:** {media} &nbsp;|&nbsp; 📅 **Fecha:** `{dt}` &nbsp;|&nbsp; 🏷️ **Categoría:** {topic}")

                    # Título destacado
                    st.markdown(f"### {title}")

                    # Breve resumen claramente legible
                    st.markdown(f"**Resumen:** {summary}")

                    st.markdown("---")

                    # Acciones: Abrir enlace y copiar enlace fácilmente
                    btn_col, copy_col = st.columns([1, 2])
                    with btn_col:
                        st.link_button("🌐 Abrir Noticia Original", url=link, type="primary", use_container_width=True)
                    with copy_col:
                        st.caption("📋 Haz clic en el icono de copiar del recuadro para copiar el enlace:")
                        st.code(link, language=None)

        # ----------------- PESTAÑA 2: TABLA NATIVA DE DATOS -----------------
        with tab_table:
            table_data = []
            for item in filtered:
                table_data.append({
                    "Ámbito": "🇪🇸 Nacional" if item.get("scope") == "Nacional" else "🌍 Internacional",
                    "Medio": item.get("media", "N/A"),
                    "Fecha": item.get("date", ""),
                    "Título": item.get("title", ""),
                    "Breve Resumen": item.get("short_summary", ""),
                    "Enlace": item.get("link", "")
                })

            df = pd.DataFrame(table_data)

            st.dataframe(
                df,
                column_config={
                    "Enlace": st.column_config.LinkColumn(
                        "Enlace Directo",
                        help="Haz clic para abrir la noticia original",
                        display_text="Abrir Noticia ↗"
                    ),
                    "Breve Resumen": st.column_config.TextColumn("Breve Resumen", width="large"),
                    "Título": st.column_config.TextColumn("Título", width="medium"),
                    "Medio": st.column_config.TextColumn("Medio", width="small"),
                    "Fecha": st.column_config.DateColumn("Fecha", width="small"),
                    "Ámbito": st.column_config.TextColumn("Ámbito", width="small"),
                },
                hide_index=True,
                use_container_width=True
            )

    else:
        st.info("No se encontraron noticias que coincidan con los filtros seleccionados.")

else:
    st.info("👆 Selecciona una fecha en el panel lateral y pulsa 'Buscar e Investigar con el Agente' para comenzar.")
