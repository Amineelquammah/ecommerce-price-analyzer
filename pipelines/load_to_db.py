# -*- coding: utf-8 -*-
import os
DB_HOST = os.getenv("DB_HOST")
os.environ["PYTHONIOENCODING"] = "utf-8"
os.environ["PGCLIENTENCODING"] = "UTF8"
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
import logging
import psycopg2
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config import (
    DB_HOST,
    DB_NAME,
    DB_USER,
    DB_PASSWORD,
    DB_PORT,
    SILVER_BUCKET
)


from utils.minio_client import read_df


# 🔥 FORCE UTF-8 (important sous Windows)
os.environ["PGCLIENTENCODING"] = "UTF8"

logging.basicConfig(level=logging.INFO)

# --------------------------------------
# LOAD
# --------------------------------------
def load_from_minio():
    logging.info("📥 Lecture depuis MinIO (silver)...")

    df = read_df(SILVER_BUCKET, "jumia/jumia_clean.csv")

    if df is None or df.empty:
        raise Exception("❌ fichier vide")

    return df

# --------------------------------------
# CLEAN FINAL
# --------------------------------------
def clean_data(df):
    logging.info("🧹 Nettoyage final...")

    def fix_encoding(x):
        if isinstance(x, str):
            return x.encode("utf-8", "ignore").decode("utf-8").strip()
        return x

    # 🔥 Fix global encoding
    df = df.apply(lambda col: col.map(fix_encoding))

    # Dates
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"])

    # Prix
    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    df = df.dropna(subset=["price"])

    # Doublons
    df = df.drop_duplicates(subset=["name", "date"])

    logging.info(f"✅ Lignes finales: {len(df)}")

    return df

# --------------------------------------
# INSERT
# --------------------------------------
def insert_to_db(df):
    logging.info("🗄️ Connexion PostgreSQL...")

    conn = psycopg2.connect(
        host=DB_HOST,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        port=DB_PORT,
        client_encoding="utf8"
    )

    cursor = conn.cursor()

    data = [
        (row["name"], row["price"], row["source"], row["date"])
        for _, row in df.iterrows()
    ]

    query = """
        INSERT INTO products (name, price, source, date)
        VALUES %s
        ON CONFLICT (name, date) DO NOTHING;
    """

    execute_values(cursor, query, data)

    conn.commit()
    cursor.close()
    conn.close()

    logging.info("✅ Données insérées")

# --------------------------------------
# MAIN
# --------------------------------------
def run_pipeline():
    df = load_from_minio()
    df = clean_data(df)
    insert_to_db(df)

if __name__ == "__main__":
    run_pipeline()