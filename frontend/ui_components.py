"""Componentes de UI reutilizáveis para o dashboard."""
import html
from urllib.parse import urlparse

import pandas as pd
import streamlit as st

DARK_CARD = "#1E1E24"
BORDER = "#333"


def inject_global_css():
    st.markdown("""
        <style>
            :root {
                --app-bg: #0b1017;
                --panel-bg: #111923;
                --panel-soft: #172230;
                --line: #263646;
                --text: #edf4f7;
                --muted: #8fa2ad;
                --accent: #55d6be;
            }
            .stApp { background: var(--app-bg); color: var(--text); }
            h1, h2, h3 { font-family: 'Helvetica Neue', sans-serif; letter-spacing: 0; }
            section[data-testid="stSidebar"] {
                background: var(--panel-bg);
                border-right: 1px solid var(--line);
            }
            section[data-testid="stSidebar"] > div {
                padding: 1.35rem 1rem 1.5rem;
            }
            section[data-testid="stSidebar"] h2 {
                color: var(--text);
                font-size: 1.05rem;
                font-weight: 700;
                margin: 0 0 1rem;
            }
            section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
                color: var(--muted);
            }
            section[data-testid="stSidebar"] hr {
                border-color: var(--line);
                margin: 1rem 0;
            }
            section[data-testid="stSidebar"] [data-testid="stPageLink"] a {
                background: var(--panel-soft);
                border: 1px solid var(--line);
                border-radius: 8px;
                color: var(--text);
                font-weight: 600;
                padding: .62rem .75rem;
                transition: background .15s ease, border-color .15s ease;
            }
            section[data-testid="stSidebar"] [data-testid="stPageLink"] a:hover {
                background: #1d2c3b;
                border-color: var(--accent);
            }
            section[data-testid="stSidebar"] [data-testid="stWidgetLabel"] label {
                color: var(--muted);
                font-size: .78rem;
                font-weight: 700;
                letter-spacing: .04em;
                text-transform: uppercase;
            }
            section[data-testid="stSidebar"] [data-baseweb="select"] > div,
            section[data-testid="stSidebar"] [data-baseweb="input"] > div {
                background: var(--panel-soft);
                border-color: var(--line);
                border-radius: 8px;
            }
            section[data-testid="stSidebar"] button[kind="primary"] {
                background: var(--accent);
                border: 0;
                color: #08201d;
                font-weight: 700;
            }
            section[data-testid="stSidebar"] button[kind="secondary"] {
                background: var(--panel-soft);
                border: 1px solid var(--line);
                color: var(--text);
                border-radius: 8px;
            }
            div[data-testid="stMetric"] {
                background: var(--panel-bg); padding: 15px;
                border-radius: 8px; border: 1px solid var(--line);
                box-shadow: 0 8px 24px rgba(0,0,0,.14);
                height: 100px; justify-content: center;
            }
            div[data-testid="stMetricLabel"] { color: var(--muted); font-size: 14px; }
            div[data-testid="stMetricValue"] { font-size: 24px; color: var(--text); }
        </style>
    """, unsafe_allow_html=True)


def book_card_html(label: str, title: str, pages: int | float, cover_url: str | None) -> str:
    safe_title = html.escape(str(title), quote=True)
    cover_value = str(cover_url).strip() if cover_url and not pd.isna(cover_url) else ""
    parsed_cover_url = urlparse(cover_value)
    if parsed_cover_url.scheme in {"http", "https"} and parsed_cover_url.netloc:
        safe_cover_url = html.escape(cover_value, quote=True)
        cover_html = f'<img src="{safe_cover_url}" style="height:75px;width:auto;border-radius:4px;object-fit:cover;">'
    else:
        cover_html = '<div style="width:50px;height:75px;background:#333;border-radius:4px;display:flex;align-items:center;justify-content:center;color:#555;font-size:10px;">Sem Capa</div>'
    return f'''<div style="background:{DARK_CARD};border:1px solid {BORDER};border-radius:8px;padding:10px;display:flex;align-items:center;height:100px;overflow:hidden;box-shadow:0 4px 6px rgba(0,0,0,0.3);"><div style="flex-shrink:0;margin-right:12px;">{cover_html}</div><div style="display:flex;flex-direction:column;justify-content:center;width:100%;overflow:hidden;"><div style="font-size:11px;color:#888;text-transform:uppercase;margin-bottom:4px;letter-spacing:0.5px;">{label}</div><div style="font-size:14px;color:#FFF;font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;" title="{safe_title}">{safe_title}</div><div style="font-size:13px;color:#CCC;margin-top:2px;">{int(pages)} páginas</div></div></div>'''


def books_summary_card_html(c_quero: int, c_lendo: int, c_relendo: int, c_lidos: int) -> str:
    return f'''<div style="background:{DARK_CARD};border:1px solid {BORDER};border-radius:8px;padding:10px 15px;height:100px;box-shadow:0 4px 6px rgba(0,0,0,0.3);display:flex;flex-direction:column;justify-content:center;"><div style="font-size:14px;color:#AAAAAA;margin-bottom:5px;">Livros</div><div style="display:flex;flex-direction:row;justify-content:space-between;width:100%;font-size:13px;color:#FAFAFA;line-height:1.5;"><div style="flex:1;"><span style="color:#90EE90;">⬤</span> Quero ler: <b>{c_quero}</b><br><span style="color:#FFD700;">⬤</span> Lendo: <b>{c_lendo}</b></div><div style="flex:1;padding-left:10px;border-left:1px solid {BORDER};"><span style="color:#ADD8E6;">⬤</span> Relendo: <b>{c_relendo}</b><br><span style="color:#FF6347;">⬤</span> Lidos: <b>{c_lidos}</b></div></div></div>'''
