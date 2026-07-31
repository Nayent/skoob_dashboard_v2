"""
Dashboard Skoob — ponto de entrada do Streamlit.
Execute com:  streamlit run load_data.py
"""
import datetime
import subprocess
import sys
import time

import streamlit as st

from config import PROJECT_DIR
from frontend.charts import (
    pending_goal_section,
    reading_timeline,
    top_authors,
    authors_rating_table,
    top_publishers,
)
from frontend.data_layer import apply_goal_logic, load_raw, process, resolve_col
from frontend.ui_components import (
    book_card_html,
    books_summary_card_html,
    inject_global_css,
)
from data_collection.storage import load_metadata, update_user_metadata

# ---------------------------------------------------------------------------
# Página
# ---------------------------------------------------------------------------
st.set_page_config(page_title="Skoob Dashboard", layout="wide", page_icon="📚")
inject_global_css()

def format_datetime(value: str | None) -> str:
    if not value:
        return "ainda nao atualizado"
    try:
        parsed = datetime.datetime.fromisoformat(value)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=datetime.timezone.utc)
        local_time = parsed.astimezone(datetime.timezone(datetime.timedelta(hours=-3)))
        return local_time.strftime("%d/%m/%Y %H:%M:%S")
    except ValueError:
        return value

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("📚 Skoob Dashboard")
    st.page_link(
        "pages/usuarios.py",
        label="Gerenciar usuários",
        icon="👥",
        use_container_width=True,
    )
    st.markdown("---")
    st.markdown("**Usuário ativo**")

    metadata_store = load_metadata()
    configured_users = {
        user_id: user_data.get("name", user_id)
        for user_id, user_data in metadata_store.get("users", {}).items()
    }

    all_user_ids = set(configured_users)
    if not all_user_ids:
        st.info("Adicione um usuario para abrir a dashboard.")
        st.stop()

    def user_label(user_id: str) -> str:
        return f"{configured_users.get(user_id, user_id)} ({user_id})"

    selected_user = st.selectbox(
        "Usuario",
        sorted(all_user_ids, key=lambda user_id: user_label(user_id).lower()),
        format_func=user_label,
        index=None,
        placeholder="Selecione um usuario...",
    )

    if selected_user is None:
        st.info("Selecione um usuario para visualizar a dashboard.")
        st.stop()

    metadata = load_metadata().get("users", {}).get(selected_user, {})
    updated_at = metadata.get("updated_at")
    cache_key = str(updated_at or "")

    st.caption(f"Última atualização · {format_datetime(updated_at)}")
    st.markdown("**Visualização**")
    is_running = metadata.get("status") in {"queued", "running"}
    if st.button("Atualizar dados", disabled=is_running, use_container_width=True):
        update_user_metadata(selected_user, status="queued", error=None)
        subprocess.Popen(
            [sys.executable, "-m", "data_collection.collector", "--user-id", selected_user],
            cwd=PROJECT_DIR,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        st.rerun()

    if is_running:
        with st.spinner("Atualizando dados..."):
            time.sleep(1)
        st.rerun()

    if metadata.get("status") == "error":
        st.error(f"Falha na ultima atualizacao: {metadata.get('error', 'erro desconhecido')}")

    raw_all, raw_goal = load_raw(selected_user, cache_key)
    widget_version = f"{selected_user}_{cache_key}"
    mode_key = f"modo_view_{widget_version}"
    year_key = f"ano_{widget_version}"
    current_year = datetime.datetime.now().year

    def sync_mode_filters() -> None:
        if st.session_state[mode_key] == "Meta de Leitura Atual":
            st.session_state[year_key] = current_year
        else:
            st.session_state[year_key] = "Todos"

    def switch_to_history() -> None:
        st.session_state[mode_key] = "Histórico Completo"

    modo_view = st.radio(
        "Visualizar:",
        ["Histórico Completo", "Meta de Leitura Atual"],
        key=mode_key,
        on_change=sync_mode_filters,
    )

    if modo_view == "Meta de Leitura Atual":
        df_main = apply_goal_logic(process(raw_goal))
        df_list_base = process(raw_goal)
        st.caption("Meta de leitura atual")
    else:
        df_main = process(raw_all)
        df_list_base = process(raw_all)
        st.caption("Histórico completo")

    st.divider()

    # Filtro por ano
    anos_disponiveis: list[int] = []
    if "read_year" in df_main.columns:
        anos_disponiveis = sorted(
            [int(x) for x in df_main["read_year"].dropna().unique()],
            reverse=True,
        )

    if modo_view == "Meta de Leitura Atual":
        st.session_state[year_key] = current_year

    opcoes_ano = ["Todos"] + sorted(
        set(anos_disponiveis) | {current_year},
        reverse=True,
    )
    ano_selecionado: int | str = st.selectbox(
        "Ano de Conclusão",
        opcoes_ano,
        key=year_key,
        on_change=switch_to_history,
        disabled=modo_view == "Meta de Leitura Atual",
    )

    # Filtro por status
    st.markdown("**Filtros da lista**")
    status_disponiveis: list[str] = []
    if "status" in df_list_base.columns:
        status_disponiveis = sorted(df_list_base["status"].dropna().unique().tolist())
    status_selecionados: list[str] = st.multiselect(
        "Status",
        status_disponiveis,
        default=status_disponiveis,
        key=f"status_{widget_version}",
    )

if raw_all.empty and raw_goal.empty:
    st.info("Nenhum dado no stage para este usuario. Clique em 'Atualizar dados'.")
    st.stop()

# ---------------------------------------------------------------------------
# Aplicação do filtro de ano nos indicadores e gráficos
# ---------------------------------------------------------------------------
df = df_main.copy()
df_goal_processed = process(raw_goal)

if ano_selecionado != "Todos":
    # read_year é Int64 (nullable); compara como int
    df = df[df["read_year"] == int(ano_selecionado)]

if modo_view == "Histórico Completo" and ano_selecionado != "Todos" and "status" in df.columns:
    df = df[df["status"] == "read"]

# Gráficos e rankings do histórico representam apenas livros finalizados.
df_visual = df
if modo_view == "Histórico Completo" and "status" in df_visual.columns:
    df_visual = df_visual[df_visual["status"] == "read"]

# Status é aplicado somente na Lista Completa.
df_list = df_list_base.copy()
if modo_view != "Meta de Leitura Atual" and ano_selecionado != "Todos" and "read_year" in df_list.columns:
    df_list = df_list[df_list["read_year"] == int(ano_selecionado)]
if "status" in df_list.columns:
    df_list = df_list[df_list["status"].isin(status_selecionados)]

# Resolução de colunas: a lista pode ter dados mesmo quando a meta não tem finalizados.
column_source = df_list_base if not df_list_base.empty else df
col_title     = resolve_col(column_source, "title")
col_author    = resolve_col(column_source, "author")
col_pages     = resolve_col(column_source, "pages")
col_rating    = resolve_col(column_source, "rating")
col_publisher = resolve_col(column_source, "publisher")
col_cover     = resolve_col(column_source, "cover")

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
title_context = modo_view
if modo_view == "Histórico Completo" and ano_selecionado != "Todos":
    title_context = f"Ano {ano_selecionado}"
st.title(f"📚 Skoob Dashboard — {title_context}")

# ---------------------------------------------------------------------------
# KPIs
# ---------------------------------------------------------------------------
n_kpis = 5 if modo_view == "Meta de Leitura Atual" or ano_selecionado != "Todos" else 4
kpi_cols = st.columns(n_kpis)

# 1. Resumo de status ou total de livros lidos no ano selecionado
if modo_view == "Histórico Completo" and ano_selecionado != "Todos":
    livros_lidos_no_ano = (
        int((df["status"] == "read").sum())
        if "status" in df.columns
        else 0
    )
    kpi_cols[0].metric("Livros lidos", livros_lidos_no_ano)
else:
    counts = df_main["status"].value_counts() if "status" in df_main.columns else {}
    kpi_cols[0].markdown(
        books_summary_card_html(
            c_quero  = int(counts.get("want_to_read", 0)) + int(counts.get("to_read", 0)),
            c_lendo  = int(counts.get("reading", 0)),
            c_relendo= int(counts.get("rereading", 0)),
            c_lidos  = int(counts.get("read", 0)),
        ),
        unsafe_allow_html=True,
    )

# 2. Páginas lidas (filtrado)
if modo_view == "Meta de Leitura Atual" and "status" in df_goal_processed.columns:
    df_pages = df_goal_processed[
        df_goal_processed["status"].isin({"read", "reading", "rereading"})
    ]
else:
    if "status" in df.columns:
        df_pages = df[df["status"].isin({"read", "reading", "rereading"})]
    else:
        df_pages = df
total_paginas = df_pages["pages_read_calc"].sum() if "pages_read_calc" in df_pages.columns else 0
kpi_cols[1].metric("Páginas Lidas", f"{total_paginas:,.0f}".replace(",", "."))

# 3 & 4. Maior e menor livro
df_books_kpi = df
if modo_view == "Histórico Completo" and "status" in df_books_kpi.columns:
    df_books_kpi = df_books_kpi[df_books_kpi["status"] == "read"]

if not df_books_kpi.empty and col_pages and col_title:
    df_com_paginas = df_books_kpi[df_books_kpi[col_pages] > 0]

    if not df_com_paginas.empty:
        for idx, label in [(df_com_paginas[col_pages].idxmax(), "Maior Livro"),
                           (df_com_paginas[col_pages].idxmin(), "Menor Livro")]:
            row = df_com_paginas.loc[idx]
            cover = row[col_cover] if col_cover else None
            kpi_cols[2 if label == "Maior Livro" else 3].markdown(
                book_card_html(label, row[col_title], row[col_pages], cover),
                unsafe_allow_html=True,
            )
    else:
        kpi_cols[2].metric("Maior Livro", "—")
        kpi_cols[3].metric("Menor Livro", "—")
else:
    kpi_cols[2].metric("Maior Livro", "—")
    kpi_cols[3].metric("Menor Livro", "—")

# 5. Ritmo (somente Meta)
if modo_view == "Meta de Leitura Atual":
    dia_ano = datetime.datetime.now().timetuple().tm_yday
    ritmo = total_paginas / dia_ano if dia_ano > 0 else 0
    kpi_cols[4].metric("Ritmo Atual", f"{ritmo:.1f} págs/dia")
elif ano_selecionado != "Todos":
    kpi_cols[4].metric("Pace no ano", f"{total_paginas / 365:.1f} págs/dia")

st.markdown("---")

# ---------------------------------------------------------------------------
# Gráficos — linha 1
# ---------------------------------------------------------------------------
if not df.empty:
    g1, g2 = st.columns(2)

    with g1:
        reading_timeline(df_visual, ano_selecionado, modo_view == "Meta de Leitura Atual")

    with g2:
        top_authors(df_visual, col_author)

# ---------------------------------------------------------------------------
# Gráficos — linha 2
# ---------------------------------------------------------------------------
if not df.empty:
    g3, g4 = st.columns(2)

    with g3:
        top_publishers(df_visual, col_publisher)

    with g4:
        authors_rating_table(df_visual, col_author, col_rating)

st.markdown("---")

# ---------------------------------------------------------------------------
# Top 10 Melhores Avaliados
# ---------------------------------------------------------------------------
st.markdown("### ⭐ Top 10 Melhores Avaliados")
if not df_visual.empty and col_rating:
    sort_columns = [col_rating]
    sort_directions = [False]
    if "finished_at" in df_visual.columns:
        sort_columns.append("finished_at")
        sort_directions.append(False)

    df_top = (
        df_visual[df_visual[col_rating] > 0]
        .sort_values(sort_columns, ascending=sort_directions, na_position="last")
        .head(10)
    )
    if not df_top.empty:
        cols_top = [
            c for c in [col_cover, col_title, col_author, col_rating, "finished_at", col_pages]
            if c and c in df_top.columns
        ]
        col_cfg = {}
        if col_cover:     col_cfg[col_cover]     = st.column_config.ImageColumn("Capa")
        if col_title:     col_cfg[col_title]     = st.column_config.TextColumn("Título")
        if col_author:    col_cfg[col_author]    = st.column_config.TextColumn("Autor")
        if col_rating:    col_cfg[col_rating]    = st.column_config.NumberColumn("Nota", format="%.1f ⭐")
        if "finished_at" in df_top.columns:
            col_cfg["finished_at"] = st.column_config.DateColumn(
                "Finalizado em",
                format="DD/MM/YYYY",
            )
        if col_pages:     col_cfg[col_pages]     = st.column_config.NumberColumn("Páginas", format="%d")

        st.dataframe(df_top[cols_top], use_container_width=True, hide_index=True, column_config=col_cfg)
    else:
        st.info("Nenhuma avaliação encontrada.")

if modo_view == "Meta de Leitura Atual":
    pending_goal_section(process(raw_goal))

# ---------------------------------------------------------------------------
# Lista Completa
# ---------------------------------------------------------------------------
st.markdown("### 📋 Lista Completa")
if not df_list.empty:
    desired = [col_cover, col_title, col_author, col_rating, col_pages, "progress", "finished_at", "status"]
    cols_view = [c for c in desired if c and c in df_list.columns]
    col_cfg_full = {}
    if col_cover:  col_cfg_full[col_cover]  = st.column_config.ImageColumn("Capa")
    if col_title:  col_cfg_full[col_title]  = st.column_config.TextColumn("Título", width="medium")
    if col_rating: col_cfg_full[col_rating] = st.column_config.NumberColumn("Nota", format="%.1f ⭐")
    if "progress" in df_list.columns:
        col_cfg_full["progress"] = st.column_config.ProgressColumn(
            "Progresso", format="%.0f%%", min_value=0, max_value=100
        )
    if "finished_at" in df_list.columns:
        col_cfg_full["finished_at"] = st.column_config.DateColumn("Concluído em", format="DD/MM/YYYY")

    st.dataframe(df_list[cols_view], use_container_width=True, hide_index=True, column_config=col_cfg_full)
