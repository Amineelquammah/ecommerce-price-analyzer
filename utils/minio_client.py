from minio import Minio
from io import BytesIO
import pandas as pd
import logging

from config import MINIO_ENDPOINT, MINIO_ACCESS_KEY, MINIO_SECRET_KEY

logging.basicConfig(level=logging.INFO)

# --------------------------------------
# INITIALISATION CLIENT
# --------------------------------------
client = Minio(
    MINIO_ENDPOINT,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=False
)

# --------------------------------------
# CREER BUCKET SI N'EXISTE PAS
# --------------------------------------
def ensure_bucket(bucket_name):
    if not client.bucket_exists(bucket_name):
        client.make_bucket(bucket_name)
        logging.info(f"🪣 Bucket créé: {bucket_name}")

# --------------------------------------
# UPLOAD DATAFRAME → MINIO
# --------------------------------------
def upload_df(bucket, object_name, df):
    try:
        ensure_bucket(bucket)

        csv_buffer = BytesIO()
        df.to_csv(csv_buffer, index=False, encoding="utf-8-sig")
        csv_buffer.seek(0)

        client.put_object(
            bucket,
            object_name,
            data=csv_buffer,
            length=csv_buffer.getbuffer().nbytes,
            content_type="text/csv"
        )

        logging.info(f"✅ Upload réussi: {bucket}/{object_name}")

    except Exception as e:
        logging.error(f"❌ Erreur upload MinIO: {e}")
        raise

# --------------------------------------
# LECTURE DATAFRAME ← MINIO
# --------------------------------------
def read_df(bucket, object_name):
    try:
        logging.info(f"📥 Lecture: {bucket}/{object_name}")

        response = client.get_object(bucket, object_name)
        data = response.read()

        df = pd.read_csv(BytesIO(data), encoding="utf-8-sig")

        logging.info(f"📊 Lignes chargées: {len(df)}")

        return df

    except Exception as e:
        logging.error(f"❌ Erreur lecture MinIO: {e}")
        raise