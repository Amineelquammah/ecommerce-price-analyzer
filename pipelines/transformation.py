import pandas as pd
from io import BytesIO
from minio import Minio
import re

from governance.schema_validation import validate_columns
from governance.quality_checks import (
    check_empty_dataframe,
    check_nulls,
    check_duplicates,
    check_price_quality
)
from governance.monitoring import logger

# ======================================
# CONFIG
# ======================================

MINIO_ENDPOINT = "localhost:9000"
MINIO_ACCESS_KEY = "admin"
MINIO_SECRET_KEY = "password"

BUCKET_BRONZE = "bronze"
BUCKET_SILVER = "silver"

SILVER_FILE = "jumia/jumia_clean.csv"

# ======================================
# MINIO CLIENT
# ======================================

def get_minio_client():

    return Minio(
        MINIO_ENDPOINT,
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
        secure=False
    )

# ======================================
# LOAD DATA
# ======================================

def load_from_minio():

    logger.info("🚀 BRONZE → SILVER PIPELINE STARTED")

    client = get_minio_client()

    logger.info("📥 Reading bronze files from MinIO")

    objects = list(
        client.list_objects(
            BUCKET_BRONZE,
            prefix="jumia/",
            recursive=True
        )
    )

    objects = sorted(
        objects,
        key=lambda o: o.object_name,
        reverse=True
    )

    if not objects:
        raise Exception("❌ No files found in bronze/jumia/")

    all_dfs = []

    for obj in objects:

        logger.info(f"📄 Reading file: {obj.object_name}")

        response = client.get_object(
            BUCKET_BRONZE,
            obj.object_name
        )

        data = response.read()

        df = pd.read_csv(
            BytesIO(data),
            encoding="latin-1"
        )

        # ======================================
        # FIX BOM / CLEAN COLUMN NAMES
        # ======================================

        df.columns = [
            c.replace("ï»¿", "").strip()
            for c in df.columns
        ]

        all_dfs.append(df)

    # ======================================
    # CONCAT
    # ======================================

    df_all = pd.concat(
        all_dfs,
        ignore_index=True
    )

    logger.info(f"📊 Total loaded rows: {len(df_all)}")

    # ======================================
    # GOVERNANCE — SCHEMA VALIDATION
    # ======================================

    required_columns = [
        "name",
        "price_raw",
        "date"
    ]

    validate_columns(
        df_all,
        required_columns,
        "jumia_bronze"
    )

    # ======================================
    # GOVERNANCE — QUALITY CHECKS
    # ======================================

    check_empty_dataframe(
        df_all,
        "jumia_bronze"
    )

    check_nulls(
        df_all,
        ["name", "price_raw"],
        "jumia_bronze"
    )

    check_duplicates(
        df_all,
        ["name", "date"],
        "jumia_bronze"
    )

    return df_all

# ======================================
# CLEAN DATA
# ======================================

def clean_data(df):

    logger.info("🧹 Advanced cleaning started")

    initial_rows = len(df)

    # ======================================
    # ENCODING FIX
    # ======================================

    def fix_encoding(x):

        if isinstance(x, str):

            return (
                x.encode("utf-8", "ignore")
                .decode("utf-8")
                .strip()
            )

        return x

    # ======================================
    # PRODUCT NAME CLEANING
    # ======================================

    def clean_name(name):

        if not isinstance(name, str):
            return name

        name = name.lower()

        name = re.sub(
            r"[^\w\s]",
            " ",
            name
        )

        name = re.sub(
            r"\s+",
            " ",
            name
        )

        return name.strip()

    # ======================================
    # APPLY ENCODING FIX
    # ======================================

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

    df = df.dropna(subset=["date"])

    # ======================================
    # PRICE CLEANING
    # ======================================

    df["price"] = (
        df["price_raw"]
        .astype(str)
        .str.replace("Dhs", "", regex=False)
        .str.replace(",", "", regex=False)
        .str.strip()
    )

    df["price"] = pd.to_numeric(
        df["price"],
        errors="coerce"
    )

    df = df.dropna(subset=["price"])

    # ======================================
    # PRICE VALIDATION
    # ======================================

    df = df[df["price"] > 0]

    check_price_quality(
        df,
        "price"
    )

    # ======================================
    # OUTLIER REMOVAL
    # ======================================

    Q1 = df["price"].quantile(0.25)
    Q3 = df["price"].quantile(0.75)

    IQR = Q3 - Q1

    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR

    df = df[
        (df["price"] >= lower_bound) &
        (df["price"] <= upper_bound)
    ]

    # ======================================
    # PRODUCT NAME NORMALIZATION
    # ======================================

    df["name_clean"] = df["name"].apply(clean_name)

    # ======================================
    # REMOVE DUPLICATES
    # ======================================

    before_duplicates = len(df)

    df = df.drop_duplicates(
        subset=["name_clean", "date"]
    )

    after_duplicates = len(df)

    logger.info(
        f"🧹 Removed duplicates: "
        f"{before_duplicates - after_duplicates}"
    )

    # ======================================
    # FINAL STATS
    # ======================================

    final_rows = len(df)

    logger.info(
        f"""
        📊 DATA QUALITY REPORT
        ----------------------
        Initial rows: {initial_rows}
        Final rows: {final_rows}
        Removed rows: {initial_rows - final_rows}

        Average price: {round(df['price'].mean(), 2)}
        Median price: {round(df['price'].median(), 2)}

        Unique products:
        {df['name_clean'].nunique()}
        """
    )

    return df

# ======================================
# SAVE TO SILVER
# ======================================

def save_to_minio(df):

    logger.info("💾 Saving cleaned data to silver layer")

    client = get_minio_client()

    csv_buffer = BytesIO()

    df.to_csv(
        csv_buffer,
        index=False,
        encoding="utf-8-sig"
    )

    csv_buffer.seek(0)

    client.put_object(
        BUCKET_SILVER,
        SILVER_FILE,
        csv_buffer,
        length=csv_buffer.getbuffer().nbytes,
        content_type="text/csv"
    )

    logger.info("✅ Silver layer successfully updated")

# ======================================
# MAIN PIPELINE
# ======================================

def run_pipeline():

    try:

        logger.info("🚀 Pipeline execution started")

        df = load_from_minio()

        df = clean_data(df)

        save_to_minio(df)

        logger.info("✅ Pipeline completed successfully")

    except Exception as e:

        logger.error(
            f"❌ Pipeline failed: {str(e)}"
        )

        raise

# ======================================
# ENTRYPOINT
# ======================================

if __name__ == "__main__":

    run_pipeline()