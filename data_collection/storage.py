"""Persistência do catálogo de usuários e do estado das atualizações."""
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from config import STAGE_DIR

METADATA_PATH = Path(STAGE_DIR) / "metadata.json"
_CSV_PATTERN = re.compile(r"^(?:all|goal)_books_(.+)\.csv$")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def load_metadata() -> dict[str, Any]:
    if not METADATA_PATH.exists():
        return {"users": {}}
    try:
        with METADATA_PATH.open("r", encoding="utf-8") as file:
            data = json.load(file)
        if isinstance(data, dict) and isinstance(data.get("users"), dict):
            allowed_fields = {"user_id", "name", "status", "error", "updated_at"}
            data["users"] = {
                user_id: {
                    key: value
                    for key, value in user_data.items()
                    if key in allowed_fields
                }
                for user_id, user_data in data["users"].items()
                if isinstance(user_data, dict)
            }
            return data
    except (OSError, json.JSONDecodeError):
        pass
    return {"users": {}}


def save_metadata(data: dict[str, Any]) -> None:
    METADATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = METADATA_PATH.with_suffix(".tmp")
    with temporary_path.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)
        file.write("\n")
    os.replace(temporary_path, METADATA_PATH)


def update_user_metadata(user_id: str, **values: Any) -> dict[str, Any]:
    data = load_metadata()
    user_data = data["users"].setdefault(user_id, {})
    user_data.update({
        key: value
        for key, value in values.items()
        if key in {"name", "status", "error"}
    })
    user_data["user_id"] = user_id
    user_data["updated_at"] = now_iso()
    save_metadata(data)
    return user_data


def create_user(user_id: str, name: str) -> dict[str, Any]:
    user_id = user_id.strip()
    name = name.strip()
    if not user_id or not name:
        raise ValueError("Informe o ID e o nome do usuario.")
    if not re.fullmatch(r"[A-Za-z0-9_-]+", user_id):
        raise ValueError("O ID deve conter apenas letras, numeros, '_' ou '-'.")
    data = load_metadata()
    if user_id in data["users"]:
        raise ValueError("Ja existe um usuario com este ID.")
    user_data = {
        "user_id": user_id,
        "name": name,
        "status": "",
        "error": None,
        "updated_at": now_iso(),
    }
    data["users"][user_id] = user_data
    save_metadata(data)
    return user_data


def update_user(user_id: str, name: str) -> dict[str, Any]:
    name = name.strip()
    if not name:
        raise ValueError("Informe o nome do usuario.")
    data = load_metadata()
    if user_id not in data["users"]:
        raise ValueError("Usuario nao encontrado.")
    user_data = data["users"][user_id]
    user_data["name"] = name
    user_data["updated_at"] = now_iso()
    save_metadata(data)
    return user_data


def delete_user(user_id: str) -> None:
    data = load_metadata()
    if user_id not in data["users"]:
        raise ValueError("Usuario nao encontrado.")
    del data["users"][user_id]
    save_metadata(data)
    for prefix in ("all_books", "goal_books"):
        csv_path = Path(STAGE_DIR) / f"{prefix}_{user_id}.csv"
        if csv_path.exists():
            csv_path.unlink()


def stage_user_ids() -> set[str]:
    if not Path(STAGE_DIR).exists():
        return set()
    user_ids: set[str] = set()
    for path in Path(STAGE_DIR).glob("*.csv"):
        match = _CSV_PATTERN.match(path.name)
        if match:
            user_ids.add(match.group(1))
    return user_ids
