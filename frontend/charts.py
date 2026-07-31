"""Gráficos do dashboard."""
import pandas as pd
import plotly.express as px
import streamlit as st

from frontend.ui_components import book_card_html

_PLOTLY_LAYOUT = dict(
    template="plotly_dark",
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
)


def reading_timeline(df: pd.DataFrame, year: int | str, current_goal: bool) -> None:
    st.markdown("### 📅 Leituras ao Longo do Tempo")
    if "finished_at" not in df.columns or not df["finished_at"].notna().any():
        st.info("Sem dados de conclusão para este filtro.")
        return
    chart_df = df.dropna(subset=["finished_at"]).copy()
    use_months = year != "Todos" or current_goal
    if use_months:
        chart_df["Periodo"] = chart_df["finished_at"].dt.to_period("M")
    else:
        chart_df["Periodo"] = chart_df["finished_at"].dt.to_period("Y")
    counts = chart_df.groupby("Periodo", sort=True).size().reset_index(name="Livros")
    if use_months:
        month_labels = {
            1: "Jan", 2: "Fev", 3: "Mar", 4: "Abr",
            5: "Mai", 6: "Jun", 7: "Jul", 8: "Ago",
            9: "Set", 10: "Out", 11: "Nov", 12: "Dez",
        }
        counts["Periodo"] = counts["Periodo"].dt.month.map(month_labels)
        period_label = "Mês"
    else:
        counts["Periodo"] = counts["Periodo"].astype(str)
        period_label = "Ano"
    fig = px.bar(counts, x="Periodo", y="Livros", text="Livros")
    fig.update_traces(marker_color="#00CC96", textposition="outside")
    fig.update_layout(
        **_PLOTLY_LAYOUT,
        xaxis={"type": "category", "title": period_label},
    )
    st.plotly_chart(fig, use_container_width=True)


def top_authors(df: pd.DataFrame, author_col: str | None) -> None:
    st.markdown("### ✍️ Livros por Autor (Top 10)")
    if not author_col:
        return
    values = df[author_col].value_counts().head(10).reset_index()
    values.columns = ["Autor", "Qtd"]
    fig = px.bar(values, x="Qtd", y="Autor", orientation="h", text="Qtd")
    fig.update_layout(**_PLOTLY_LAYOUT, yaxis={"categoryorder": "total ascending"})
    fig.update_traces(marker_color="#EF553B", textposition="outside")
    st.plotly_chart(fig, use_container_width=True)


def top_publishers(df: pd.DataFrame, publisher_col: str | None) -> None:
    st.markdown("### 🏢 Livros por Editora (Top 10)")
    if not publisher_col:
        st.info("Coluna de editora não encontrada.")
        return
    values = df[publisher_col].value_counts().head(10).reset_index()
    values.columns = ["Editora", "Qtd"]
    fig = px.bar(values, x="Qtd", y="Editora", orientation="h", text="Qtd")
    fig.update_layout(**_PLOTLY_LAYOUT, yaxis={"categoryorder": "total ascending"})
    fig.update_traces(marker_color="#AB63FA", textposition="outside")
    st.plotly_chart(fig, use_container_width=True)


def authors_rating_table(
    df: pd.DataFrame,
    author_col: str | None,
    rating_col: str | None,
) -> None:
    st.markdown("### 🏆 Melhores Autores por Média de Nota")
    if not author_col or not rating_col:
        return

    rated_books = df[df[rating_col] > 0]
    if rated_books.empty:
        st.info("Sem avaliações registradas.")
        return

    aggregations = {
        "Media": (rating_col, "mean"),
        "Livros": (rating_col, "count"),
    }
    sort_columns = ["Media", "Livros"]
    sort_directions = [False, False]
    if "finished_at" in rated_books.columns:
        aggregations["UltimaFinalizacao"] = ("finished_at", "max")
        sort_columns.append("UltimaFinalizacao")
        sort_directions.append(False)

    author_ratings = (
        rated_books.groupby(author_col)
        .agg(**aggregations)
        .reset_index()
        .sort_values(sort_columns, ascending=sort_directions, na_position="last")
        .head(10)
    )
    author_ratings.columns = ["Autor", "Media", "Livros"] + (
        ["UltimaFinalizacao"] if "UltimaFinalizacao" in author_ratings.columns else []
    )
    author_ratings = author_ratings[["Autor", "Media", "Livros"]]
    st.dataframe(
        author_ratings,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Autor": st.column_config.TextColumn("Autor"),
            "Media": st.column_config.NumberColumn("Média", format="%.1f ⭐"),
            "Livros": st.column_config.NumberColumn("Livros", format="%d"),
        },
    )


def pending_goal_section(df: pd.DataFrame) -> None:
    """Exibe o resumo do que falta ler na meta atual."""
    st.markdown("---")
    st.markdown("### 📖 O que falta ler na meta atual")

    pending_statuses = {"to_read", "want_to_read", "reading"}
    if "status" not in df.columns:
        st.info("Não há status disponíveis para calcular as pendências.")
        return

    pending = df[df["status"].isin(pending_statuses)].copy()
    if pending.empty:
        st.info("Nenhum livro pendente na meta atual.")
        return

    page_col = next((col for col in ("pages", "paginas") if col in pending.columns), None)
    if not page_col:
        st.info("Não há informação de páginas para calcular as pendências.")
        return

    pending[page_col] = pd.to_numeric(pending[page_col], errors="coerce").fillna(0)
    if "progress" in pending.columns:
        progress = pd.to_numeric(pending["progress"], errors="coerce").fillna(0).clip(0, 100)
    else:
        progress = 0
    pending["PaginasRestantes"] = pending[page_col] * (1 - progress / 100)

    total_books = len(pending)
    total_pages = pending["PaginasRestantes"].sum()
    goal_total_books = len(df)
    goal_total_pages = pd.to_numeric(df[page_col], errors="coerce").fillna(0).sum()
    completed_books = goal_total_books - total_books
    completed_pages = max(0, goal_total_pages - total_pages)
    books_progress_pct = completed_books / goal_total_books * 100 if goal_total_books else 0
    pages_progress_pct = completed_pages / goal_total_pages * 100 if goal_total_pages else 0
    books_with_pages = pending[pending[page_col] > 0]
    books_for_size = books_with_pages if not books_with_pages.empty else pending
    largest = books_for_size.loc[books_for_size[page_col].idxmax()]
    smallest = books_for_size.loc[books_for_size[page_col].idxmin()]
    title_col = next((col for col in ("title", "titulo") if col in pending.columns), None)
    cover_col = next(
        (col for col in ("cover_filename", "cover", "img_url") if col in pending.columns),
        None,
    )
    today = pd.Timestamp.now().normalize()
    end_of_year = pd.Timestamp(year=today.year, month=12, day=31)
    days_remaining = max(1, (end_of_year - today).days + 1)
    pages_per_day = total_pages / days_remaining

    progress_cols = st.columns(2)
    with progress_cols[0]:
        with st.container(border=True):
            st.metric("Progresso de páginas", f"{pages_progress_pct:.1f}%")
            st.progress(
                min(1.0, pages_progress_pct / 100),
                text=f"{completed_pages:,.0f} de {goal_total_pages:,.0f} páginas".replace(",", "."),
            )
    with progress_cols[1]:
        with st.container(border=True):
            st.metric("Progresso de livros", f"{books_progress_pct:.1f}%")
            st.progress(
                min(1.0, books_progress_pct / 100),
                text=f"{completed_books} de {goal_total_books} livros",
            )

    kpi_cols = st.columns(5)
    kpi_cols[0].metric("Livros pendentes", f"{total_books}")
    kpi_cols[1].metric("Páginas restantes", f"{total_pages:,.0f}".replace(",", "."))
    if title_col:
        kpi_cols[2].markdown(
            book_card_html(
                "Maior livro pendente",
                largest[title_col],
                largest[page_col],
                largest[cover_col] if cover_col else None,
            ),
            unsafe_allow_html=True,
        )
        kpi_cols[3].markdown(
            book_card_html(
                "Menor livro pendente",
                smallest[title_col],
                smallest[page_col],
                smallest[cover_col] if cover_col else None,
            ),
            unsafe_allow_html=True,
        )
    else:
        kpi_cols[2].metric("Maior livro", f"{largest['PaginasRestantes']:.0f} págs")
        kpi_cols[3].metric("Menor livro", f"{smallest['PaginasRestantes']:.0f} págs")
    kpi_cols[4].metric("Páginas/dia até 31/12", f"{pages_per_day:.1f}")

    chart_cols = st.columns(2)
    with chart_cols[0]:
        status_counts = (
            df["status"]
            .map({
                "read": "Lido",
                "to_read": "Quero ler",
                "want_to_read": "Quero ler",
                "reading": "Lendo",
                "rereading": "Relendo",
            })
            .fillna(df["status"])
            .value_counts()
            .rename_axis("Status")
            .reset_index(name="Livros")
        )
        fig = px.pie(
            status_counts,
            names="Status",
            values="Livros",
            hole=0.58,
            color="Status",
            color_discrete_map={
                "Lido": "#00CC96",
                "Lendo": "#FECB52",
                "Relendo": "#636EFA",
                "Quero ler": "#EF553B",
            },
        )
        fig.update_traces(textposition="inside", textinfo="label+percent")
        fig.update_layout(**_PLOTLY_LAYOUT, showlegend=True)
        st.plotly_chart(fig, use_container_width=True)

    with chart_cols[1]:
        if title_col:
            remaining_books = (
                pending[[title_col, "PaginasRestantes"]]
                .sort_values("PaginasRestantes", ascending=False)
                .head(10)
                .sort_values("PaginasRestantes")
            )
            fig = px.bar(
                remaining_books,
                x="PaginasRestantes",
                y=title_col,
                orientation="h",
                text="PaginasRestantes",
            )
            fig.update_traces(marker_color="#EF553B", texttemplate="%{text:.0f}", textposition="outside")
            fig.update_layout(
                **_PLOTLY_LAYOUT,
                height=max(360, 38 * len(remaining_books) + 100),
                xaxis_title="Páginas restantes",
                yaxis_title=None,
            )
            st.plotly_chart(fig, use_container_width=True)
