import os
import json
from pathlib import Path
from datetime import datetime

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

DB_HOST = os.getenv("POSTGRES_HOST")
DB_PORT = os.getenv("POSTGRES_PORT")
DB_NAME = os.getenv("POSTGRES_DB")
DB_USER = os.getenv("POSTGRES_USER")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_MESSAGES_DIR = BASE_DIR / "data" / "raw" / "telegram_messages"

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL)


def read_all_json_files():
    """
    This function reads every JSON file inside:
    data/raw/telegram_messages/YYYY-MM-DD/channel_name.json

    It does not care if the dates are different.
    It reads all date folders automatically.
    """

    all_records = []

    json_files = list(RAW_MESSAGES_DIR.glob("*/*.json"))

    if not json_files:
        print("No JSON files found inside data/raw/telegram_messages/")
        return all_records

    for json_file in json_files:
        scrape_date = json_file.parent.name
        source_file = str(json_file)

        with open(json_file, "r", encoding="utf-8") as f:
            records = json.load(f)

        for record in records:
            record["scrape_date"] = scrape_date
            record["source_file"] = source_file
            record["loaded_at"] = datetime.now().isoformat()

            all_records.append(record)

    return all_records


def load_to_postgres():
    records = read_all_json_files()

    if not records:
        print("No records found. Run the scraper first.")
        return

    df = pd.DataFrame(records)

    expected_columns = [
        "message_id",
        "channel_name",
        "message_date",
        "message_text",
        "has_media",
        "image_path",
        "views",
        "forwards",
        "scrape_date",
        "source_file",
        "loaded_at"
    ]

    for column in expected_columns:
        if column not in df.columns:
            df[column] = None

    df = df[expected_columns]

    with engine.begin() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS raw"))

    df.to_sql(
        "telegram_messages",
        engine,
        schema="raw",
        if_exists="replace",
        index=False
    )

    print(f"Loaded {len(df)} records into raw.telegram_messages")
    print(f"Loaded channels: {df['channel_name'].nunique()}")
    print(f"Loaded files: {df['source_file'].nunique()}")


if __name__ == "__main__":
    load_to_postgres()