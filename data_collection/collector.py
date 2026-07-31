"""Coleta dados da API e salva os CSVs na pasta stage/."""
import argparse
import os

import pandas as pd

from config import STAGE_DIR
from data_collection.api import get_data
from data_collection.storage import load_metadata, update_user_metadata


def update_user(user_id: str) -> None:
    os.makedirs(STAGE_DIR, exist_ok=True)
    user_name = load_metadata().get("users", {}).get(user_id, {}).get("name", user_id)
    update_user_metadata(user_id, name=user_name, status="running", error=None)
    try:
        print(f"Buscando todos os livros do usuario {user_id}...")
        df_all = pd.DataFrame(get_data(params={"user_id": user_id}))
        all_path = os.path.join(STAGE_DIR, f"all_books_{user_id}.csv")
        if not df_all.empty:
            df_all.to_csv(all_path, index=False, encoding="utf-8", sep="|")
            print(f"  -> {len(df_all)} livros salvos em {all_path}")

        print("Buscando livros da meta de leitura atual...")
        df_goal = pd.DataFrame(get_data(params={"user_id": user_id, "filter": "reading_goal"}))
        goal_path = os.path.join(STAGE_DIR, f"goal_books_{user_id}.csv")
        if not df_goal.empty:
            df_goal.to_csv(goal_path, index=False, encoding="utf-8", sep="|")
            print(f"  -> {len(df_goal)} livros salvos em {goal_path}")
        update_user_metadata(user_id, name=user_name, status="success", error=None)
    except Exception as exc:
        update_user_metadata(user_id, status="error", error=str(exc))
        raise


def main(user_id: str) -> None:
    update_user(user_id)
    print("Concluído.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--user-id", required=True)
    main(parser.parse_args().user_id)
