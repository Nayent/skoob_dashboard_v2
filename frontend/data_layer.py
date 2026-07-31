"""Leitura, limpeza e processamento dos CSVs para a interface."""
import datetime
import os

import pandas as pd
import streamlit as st

from config import STAGE_DIR

_COLUMN_CANDIDATES = {
    "title": ["title", "titulo"],
    "author": ["author", "autor"],
    "pages": ["pages", "paginas"],
    "rating": ["rating", "stars", "ranking"],
    "publisher": ["publisher", "editora"],
    "cover": ["cover_filename", "cover", "img_url"],
}


def resolve_col(df: pd.DataFrame, key: str) -> str | None:
    for candidate in _COLUMN_CANDIDATES.get(key, []):
        if candidate in df.columns:
            return candidate
    return None


@st.cache_data
def load_raw(user_id: str, cache_key: str = "") -> tuple[pd.DataFrame, pd.DataFrame]:
    def _read(filename: str) -> pd.DataFrame:
        for path in [os.path.join(STAGE_DIR, filename), filename]:
            if os.path.exists(path):
                try:
                    return pd.read_csv(path, sep="|", dtype=str)
                except Exception as exc:
                    st.warning(f"Erro ao ler {path}: {exc}")
        return pd.DataFrame()

    return _read(f"all_books_{user_id}.csv"), _read(f"goal_books_{user_id}.csv")


def _coerce_numeric(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    for col in cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
    return df


def process(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    df = df.copy()
    if "finished_at" in df.columns:
        df["finished_at"] = pd.to_datetime(df["finished_at"], errors="coerce")
        df["read_year"] = df["finished_at"].dt.year.astype("Int64")
    else:
        df["read_year"] = pd.NA
    for col in ["author", "autor"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace(r"\s+", " ", regex=True).str.strip()
    _coerce_numeric(df, ["pages", "rating", "progress", "stars", "ranking"])
    if "progress" in df.columns:
        df["progress"] = df["progress"].clip(0, 100)
    col_pag = resolve_col(df, "pages")
    if "progress" in df.columns and col_pag:
        df["pages_read_calc"] = (df["progress"] / 100.0) * df[col_pag]
    else:
        df["pages_read_calc"] = 0.0
    return df


def apply_goal_logic(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or "finished_at" not in df.columns:
        return df
    df = df.copy()
    current_year = datetime.datetime.now().year
    col_pag = resolve_col(df, "pages")
    old_mask = (df["finished_at"].dt.year < current_year) & df["finished_at"].notna()
    if "progress" in df.columns:
        df.loc[old_mask & (df["progress"] == 100), "progress"] = 0.0
    df.loc[old_mask, "finished_at"] = pd.NaT
    df.loc[old_mask, "read_year"] = pd.NA
    if col_pag and "progress" in df.columns:
        df["pages_read_calc"] = (df["progress"] / 100.0) * df[col_pag]
    elif col_pag:
        df["pages_read_calc"] = 0.0
    return df
