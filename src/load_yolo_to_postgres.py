from pathlib import Path
import os

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text


BASE_DIR = Path(__file__).resolve().parent.parent
CSV_PATH = BASE_DIR / "data" / "processed" / "yolo_detections.csv"

load_dotenv(BASE_DIR / ".env")

DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "medical_warehouse")
DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")

DATABASE_URL = (
    f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}"
    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)


def load_yolo_results():
    if not CSV_PATH.exists():
        raise FileNotFoundError(f"YOLO CSV not found at {CSV_PATH}")

    df = pd.read_csv(CSV_PATH)

    expected_columns = {
        "message_id",
        "channel_name",
        "image_path",
        "detected_class",
        "confidence_score",
        "image_category",
    }

    missing = expected_columns - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns in YOLO CSV: {missing}")

    df["message_id"] = df["message_id"].astype(str)
    df["channel_name"] = df["channel_name"].astype(str)
    df["image_path"] = df["image_path"].astype(str)
    df["detected_class"] = df["detected_class"].astype(str)
    df["confidence_score"] = pd.to_numeric(df["confidence_score"], errors="coerce").fillna(0.0)
    df["image_category"] = df["image_category"].astype(str)

    engine = create_engine(DATABASE_URL)

    with engine.begin() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS raw"))
        conn.execute(text("DROP TABLE IF EXISTS raw.image_detections"))

    df.to_sql(
        "image_detections",
        engine,
        schema="raw",
        if_exists="replace",
        index=False,
    )

    print(f"Loaded {len(df)} YOLO detection rows into raw.image_detections")


if __name__ == "__main__":
    load_yolo_results()