# -*- coding: utf-8 -*-
import psycopg2
import logging
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from config import DB_HOST, DB_NAME, DB_USER, DB_PASSWORD, DB_PORT

logging.basicConfig(level=logging.INFO)

def create_brand_table():
    logging.info("✨ Création GOLD layer (smart brand matching)...")

    conn = psycopg2.connect(
        f"host={DB_HOST} dbname={DB_NAME} user={DB_USER} password={DB_PASSWORD} port={DB_PORT}"
    )
    cursor = conn.cursor()

    query = """
    -- TABLE BRANDS
    DROP TABLE IF EXISTS brands;

    CREATE TABLE brands (
        brand_name TEXT
    );

    INSERT INTO brands (brand_name) VALUES
    ('samsung'),
    ('xiaomi'),
    ('apple'),
    ('itel'),
    ('infinix'),
    ('honor'),
    ('oppo'),
    ('meizu'),
    ('huawei'),
    ('realme'),
    ('vivo'),
    ('oneplus'),
    ('google pixel'),
    ('sony'),
    ('nokia'),
    ('motorola'),
    ('blackberry'),
    ('zte');
    
    


    -- GOLD
    DROP TABLE IF EXISTS brand_stats;

    CREATE TABLE brand_stats AS
    SELECT
        COALESCE(UPPER(b.brand_name), 'OTHER') AS brand,
        COUNT(*) AS observations,
        ROUND(AVG(p.price)::numeric, 2) AS avg_price,
        MIN(p.price) AS min_price,
        MAX(p.price) AS max_price,
        MAX(p.date) AS last_seen
    FROM products p
    LEFT JOIN brands b
        ON p.name ILIKE '%' || b.brand_name || '%'
    GROUP BY brand;
    """

    cursor.execute(query)
    conn.commit()

    cursor.close()
    conn.close()

    logging.info("✅ brand_stats créée avec matching intelligent")

def run_pipeline():
    create_brand_table()

if __name__ == "__main__":
    run_pipeline()