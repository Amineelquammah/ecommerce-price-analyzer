# -*- coding: utf-8 -*-

import os
import sys
import pandas as pd
import psycopg2

from psycopg2.extras import execute_values

# ======================================
# UTF-8 CONFIG
# ======================================

os.environ["PYTHONIOENCODING"] = "utf-8"
os.environ["PGCLIENTENCODING"] = "UTF8"

# ======================================
# PATH CONFIG
# ======================================

sys.path.append(
    os.path.dirname(
        os.path.dirname(__file__)
    )
)

# ======================================
# IMPORTS
# ======================================

from config import (
    DB_HOST,
    DB_NAME,
    DB_USER,
    DB_PASSWORD,
    DB_PORT,
    SILVER_BUCKET
)

from utils.minio_client import read_df

from governance.monitoring import logger

from governance.schema_validation import (
    validate_columns
)

from governance.quality_checks import (
    check_empty_dataframe,
    check_nulls,
    check_duplicates,
    check_price_quality
)

# ======================================
# LOAD
# ======================================

def load_from_minio():

    logger.info(
        "📥 Loading cleaned data from MinIO (silver)"
    )

    df = read_df(
        SILVER_BUCKET,
        "jumia/jumia_clean.csv"
    )

    if df is None or df.empty:

        logger.error("❌ Empty silver dataset")

        raise Exception("Silver dataset is empty")

    logger.info(
        f"📊 Loaded rows: {len(df)}"
    )

    # ======================================
    # GOVERNANCE — SCHEMA VALIDATION
    # ======================================

    required_columns = [
        "name",
        "price",
        "source",
        "date"
    ]

    validate_columns(
        df,
        required_columns,
        "jumia_silver"
    )

    # ======================================
    # GOVERNANCE — QUALITY CHECKS
    # ======================================

    check_empty_dataframe(
        df,
        "jumia_silver"
    )

    check_nulls(
        df,
        ["name", "price"],
        "jumia_silver"
    )

    check_duplicates(
        df,
        ["name", "date"],
        "jumia_silver"
    )

    return df

# ======================================
# CLEAN FINAL
# ======================================

def clean_data(df):

    logger.info("🧹 Final cleaning started")

    initial_rows = len(df)

    # ======================================
    # ENCODING FIX
    # ======================================

    def fix_encoding(x):

        if isinstance(x, str):

            return (
                x.encode(
                    "utf-8",
                    "ignore"
                )
                .decode("utf-8")
                .strip()
            )

        return x

    # Apply encoding fix
    df = df.apply(
        lambda col: col.map(fix_encoding)
    )

    # ======================================
    # DATE CLEANING
    # ======================================

    df["date"] = pd.to_datetime(
        df["date"],
        errors="coerce"
    )

    df = df.dropna(
        subset=["date"]
    )

    # ======================================
    # PRICE CLEANING
    # ======================================

    df["price"] = pd.to_numeric(
        df["price"],
        errors="coerce"
    )

    df = df.dropna(
        subset=["price"]
    )

    # ======================================
    # PRICE VALIDATION
    # ======================================

    df = df[df["price"] > 0]

    check_price_quality(
        df,
        "price"
    )

    # ======================================
    # REMOVE DUPLICATES
    # ======================================

    before_duplicates = len(df)

    df = df.drop_duplicates(
        subset=["name", "date"]
    )

    after_duplicates = len(df)

    logger.info(
        f"🧹 Removed duplicates: "
        f"{before_duplicates - after_duplicates}"
    )

    # ======================================
    # FINAL METRICS
    # ======================================

    final_rows = len(df)

    logger.info(
        f"""
        📊 FINAL DATA REPORT
        --------------------
        Initial rows: {initial_rows}
        Final rows: {final_rows}

        Average price:
        {round(df['price'].mean(), 2)}

        Unique products:
        {df['name'].nunique()}
        """
    )

    return df

# ======================================
# INSERT TO POSTGRES
# ======================================

def insert_to_db(df):

    logger.info(
        "🗄️ Connecting to PostgreSQL"
    )

    conn = None

    try:

        conn = psycopg2.connect(
            host=DB_HOST,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            port=DB_PORT,
            client_encoding="utf8"
        )

        cursor = conn.cursor()

        logger.info(
            "📤 Preparing batch insert"
        )

        data = [
            (
                row["name"],
                row["price"],
                row["source"],
                row["date"]
            )
            for _, row in df.iterrows()
        ]

        query = """
            INSERT INTO products (
                name,
                price,
                source,
                date
            )
            VALUES %s

            ON CONFLICT (
                name,
                date
            )
            DO NOTHING;
        """

        execute_values(
            cursor,
            query,
            data
        )

        conn.commit()

        logger.info(
            f"✅ Inserted rows: {len(data)}"
        )

        cursor.close()

    except Exception as e:

        if conn:
            conn.rollback()

        logger.error(
            f"❌ Database insert failed: {str(e)}"
        )

        raise

    finally:

        if conn:
            conn.close()

            logger.info(
                "🔒 PostgreSQL connection closed"
            )

# ======================================
# MAIN PIPELINE
# ======================================

def run_pipeline():

    try:

        logger.info(
            "🚀 GOLD PIPELINE STARTED"
        )

        df = load_from_minio()

        df = clean_data(df)

        insert_to_db(df)

        logger.info(
            "✅ GOLD PIPELINE COMPLETED"
        )

    except Exception as e:

        logger.error(
            f"❌ PIPELINE FAILED: {str(e)}"
        )

        raise

# ======================================
# ENTRYPOINT
# ======================================

if __name__ == "__main__":

    run_pipeline()