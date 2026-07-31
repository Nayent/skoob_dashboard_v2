"""Compatibilidade: o coletor está em data_collection.collector."""
import argparse

from data_collection.collector import main


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--user-id", required=True)
    main(parser.parse_args().user_id)
