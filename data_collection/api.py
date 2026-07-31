"""
Módulo de extração de dados da API do Skoob.
"""
import time
from typing import Iterator

import requests

from config import API_URL, MAX_RETRIES, PAGE_LIMIT, REQUEST_TIMEOUT, TOKEN


def _build_headers() -> dict:
    if not TOKEN:
        raise RuntimeError(
            "SKOOB_TOKEN não configurado. Defina a variável de ambiente antes de executar collector.py."
        )
    return {
        "Authorization": f"Bearer {TOKEN}",
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json",
        "Referer": "https://www.skoob.com.br/",
    }


def get_data(params: dict | None = None) -> Iterator[dict]:
    """Gera todos os itens da estante, paginando automaticamente."""
    params = dict(params or {})
    base_params = {"page": 1, "limit": PAGE_LIMIT, "bookshelf_type": "book"}
    base_params.update(params)
    headers = _build_headers()

    while True:
        retries_left = MAX_RETRIES
        try:
            response = requests.get(
                API_URL,
                params=base_params,
                headers=headers,
                timeout=REQUEST_TIMEOUT,
            )
        except requests.RequestException as exc:
            print(f"[get_data] Erro de conexão: {exc}")
            if retries_left > 0:
                retries_left -= 1
                time.sleep(2)
                continue
            break

        if response.status_code == 401:
            print("[get_data] Token expirado ou inválido. Atualize SKOOB_TOKEN.")
            break
        if response.status_code != 200:
            print(f"[get_data] HTTP {response.status_code}: {response.text[:200]}")
            if response.status_code in {429, 500, 502, 503, 504} and retries_left > 0:
                retries_left -= 1
                time.sleep(2)
                continue
            break

        try:
            data = response.json()
        except ValueError:
            print("[get_data] Resposta da API não contém JSON válido.")
            break
        if not isinstance(data, dict):
            print("[get_data] Resposta da API em formato inesperado.")
            break

        items = data.get("items", [])
        if not isinstance(items, list):
            print("[get_data] Campo 'items' em formato inesperado.")
            break
        try:
            total_pages = max(1, int(data.get("total_pages", 1)))
        except (TypeError, ValueError):
            total_pages = 1

        yield from items
        if not items or base_params["page"] >= total_pages:
            break
        base_params["page"] += 1
