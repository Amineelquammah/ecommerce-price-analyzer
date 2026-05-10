import pandas as pd
import logging
from io import BytesIO
from minio import Minio

# CONFIG
MINIO_ENDPOINT = "localhost:9000"
MINIO_ACCESS_KEY = "admin"
MINIO_SECRET_KEY = "password"

BUCKET_BRONZE = "bronze"
BUCKET_SILVER = "silver"

SILVER_FILE = "jumia/jumia_clean.csv"

logging.basicConfig(level=logging.INFO)

def get_minio_client():
    return Minio(
        MINIO_ENDPOINT,
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
        secure=False
    )

# --------------------------------------
# LOAD — tous les fichiers bronze
# --------------------------------------
def load_from_minio():
    client = get_minio_client()

    logging.info("📥 Lecture depuis MinIO (bronze)...")

    objects = list(client.list_objects(BUCKET_BRONZE, prefix="jumia/", recursive=True))
    objects = sorted(objects, key=lambda o: o.object_name, reverse=True)

    all_dfs = []

    for obj in objects:
        logging.info(f"📄 Lecture: {obj.object_name}")
        response = client.get_object(BUCKET_BRONZE, obj.object_name)
        data = response.read()
        df = pd.read_csv(BytesIO(data), encoding="latin-1")

        # 🔥 Fix BOM sur le nom de colonne
        df.columns = [c.replace("ï»¿", "").strip() for c in df.columns]

        all_dfs.append(df)

    if not all_dfs:
        raise Exception("❌ Aucun fichier trouvé dans bronze/jumia/")

    df_all = pd.concat(all_dfs, ignore_index=True)

    logging.info(f"📊 Total lignes chargées: {len(df_all)}")

    return df_all

# --------------------------------------
# CLEAN
# --------------------------------------
def clean_data(df):
    logging.info("🧹 Nettoyage avancé...")

    import re

    def fix_encoding(x):
        if isinstance(x, str):
            return x.encode("utf-8", "ignore").decode("utf-8").strip()
        return x

    def clean_name(name):
        if not isinstance(name, str):
            return name

        name = name.lower()
        name = re.sub(r"[^\w\s]", " ", name)
        name = re.sub(r"\s+", " ", name)
        return name.strip()

    # encoding
    df = df.apply(lambda col: col.map(fix_encoding))

    # date
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"])

    # price
    df["price"] = (
        df["price_raw"]
        .astype(str)
        .str.replace("Dhs", "", regex=False)
        .str.replace(",", "", regex=False)
        .str.strip()
    )

    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    df = df.dropna(subset=["price"])

    # 🔥 validation prix > 0
    df = df[df["price"] > 0]

    # 🔥 suppression outliers
    Q1 = df["price"].quantile(0.25)
    Q3 = df["price"].quantile(0.75)
    IQR = Q3 - Q1

    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR

    df = df[(df["price"] >= lower_bound) & (df["price"] <= upper_bound)]

    # 🔥 normalisation noms
    df["name_clean"] = df["name"].apply(clean_name)

    # doublons
    df = df.drop_duplicates(subset=["name_clean", "date"])

    logging.info(f"📊 Lignes finales: {len(df)}")

    return df

# --------------------------------------
# SAVE
# --------------------------------------
def save_to_minio(df):
    client = get_minio_client()

    logging.info("💾 Sauvegarde vers MinIO (silver)...")

    csv_buffer = BytesIO()
    df.to_csv(csv_buffer, index=False, encoding="utf-8-sig")
    csv_buffer.seek(0)

    client.put_object(
        BUCKET_SILVER,
        SILVER_FILE,
        csv_buffer,
        length=csv_buffer.getbuffer().nbytes,
        content_type="text/csv"
    )

    logging.info("✅ Données sauvegardées")

# --------------------------------------
# MAIN
# --------------------------------------
def run_pipeline():
    df = load_from_minio()
    df = clean_data(df)
    save_to_minio(df)

if __name__ == "__main__":
    run_pipeline()