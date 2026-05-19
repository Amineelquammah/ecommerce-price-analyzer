# -*- coding: utf-8 -*-

import psycopg2
import sys
import os

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
    DB_PORT
)

from governance.monitoring import logger

from governance.schema_validation import (
    validate_columns
)

from governance.quality_checks import (
    check_empty_dataframe,
    check_nulls,
    check_duplicates
)

# ======================================
# DB CONNECTION
# ======================================

def get_connection():

    return psycopg2.connect(
        host=DB_HOST,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        port=DB_PORT
    )

# ======================================
# GOVERNANCE CHECKS
# ======================================

def run_governance_checks(cursor):

    logger.info(
        "🛡️ Running governance checks"
    )

    # ======================================
    # CHECK EMPTY PRODUCTS TABLE
    # ======================================

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM products;
        """
    )

    total_products = cursor.fetchone()[0]

    logger.info(
        f"📊 products rows: {total_products}"
    )

    if total_products == 0:

        logger.error(
            "❌ products table is EMPTY"
        )

        raise Exception(
            "products table is EMPTY"
        )

    # ======================================
    # CHECK NULLS
    # ======================================

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM products
        WHERE name IS NULL
           OR price IS NULL
           OR date IS NULL;
        """
    )

    nulls = cursor.fetchone()[0]

    logger.info(
        f"📊 Null rows detected: {nulls}"
    )

    if nulls > 0:

        logger.warning(
            f"⚠️ Found {nulls} rows with NULL values"
        )

    # ======================================
    # CHECK DUPLICATES
    # ======================================

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM (
            SELECT name, date, COUNT(*)
            FROM products
            GROUP BY name, date
            HAVING COUNT(*) > 1
        ) duplicates;
        """
    )

    duplicates = cursor.fetchone()[0]

    logger.info(
        f"📊 Duplicate groups: {duplicates}"
    )

    if duplicates > 0:

        logger.warning(
            f"⚠️ Found {duplicates} duplicated products"
        )

    # ======================================
    # CHECK INVALID PRICES
    # ======================================

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM products
        WHERE price <= 0;
        """
    )

    invalid_prices = cursor.fetchone()[0]

    logger.info(
        f"📊 Invalid prices: {invalid_prices}"
    )

    if invalid_prices > 0:

        logger.warning(
            f"⚠️ Found {invalid_prices} invalid prices"
        )

# ======================================
# CREATE GOLD TABLE
# ======================================

def create_brand_table():

    logger.info(
        "🚀 GOLD PIPELINE STARTED"
    )

    conn = None

    try:

        conn = get_connection()

        cursor = conn.cursor()

        # ======================================
        # GOVERNANCE CHECKS
        # ======================================

        run_governance_checks(cursor)

        # ======================================
        # CREATE BRANDS TABLE
        # ======================================

        logger.info(
            "📦 Creating brands reference table"
        )

        cursor.execute(
            """

            CREATE TABLE IF NOT EXISTS brands (
                brand_name TEXT PRIMARY KEY
            );

            """
        )

        # ======================================
        # INSERT BRANDS
        # ======================================

        brands = [
            "samsung",
            "xiaomi",
            "apple",
            "itel",
            "infinix",
            "honor",
            "oppo",
            "meizu",
            "huawei",
            "realme",
            "vivo",
            "oneplus",
            "google pixel",
            "sony",
            "nokia",
            "motorola",
            "blackberry",
            "zte"
        ]

        for brand in brands:

            cursor.execute(
                """
                INSERT INTO brands (
                    brand_name
                )
                VALUES (%s)

                ON CONFLICT DO NOTHING;
                """,
                (brand,)
            )

        logger.info(
            f"✅ Inserted brands: {len(brands)}"
        )

        # ======================================
        # REFRESH GOLD TABLE
        # ======================================

        logger.info(
            "🧹 Refreshing GOLD layer"
        )

        cursor.execute(
            """
            DROP TABLE IF EXISTS brand_stats;
            """
        )

        # ======================================
        # CREATE GOLD ANALYTICS
        # ======================================

        logger.info(
            "📊 Creating brand analytics"
        )

        cursor.execute(
            """

            CREATE TABLE brand_stats AS

            SELECT

                COALESCE(
                    UPPER(b.brand_name),
                    'OTHER'
                ) AS brand,

                COUNT(*) AS observations,

                ROUND(
                    AVG(p.price)::numeric,
                    2
                ) AS avg_price,

                MIN(p.price) AS min_price,

                MAX(p.price) AS max_price,

                MAX(p.date) AS last_seen

            FROM products p

            LEFT JOIN brands b

                ON LOWER(p.name)
                LIKE '%' || LOWER(b.brand_name) || '%'

            GROUP BY brand

            ORDER BY observations DESC;

            """
        )

        conn.commit()

        logger.info(
            "✅ GOLD brand_stats created"
        )

        # ======================================
        # GOLD METRICS
        # ======================================

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM brand_stats;
            """
        )

        total_brands = cursor.fetchone()[0]

        cursor.execute(
            """
            SELECT AVG(avg_price)
            FROM brand_stats;
            """
        )

        avg_market_price = cursor.fetchone()[0]

        logger.info(
            f"""
            📊 GOLD METRICS
            ----------------
            Total brands:
            {total_brands}

            Average market price:
            {round(avg_market_price, 2)}
            """
        )

        # ======================================
        # DATA LINEAGE
        # ======================================

        logger.info(
            """
            🔄 DATA LINEAGE
            ----------------
            products table
                ↓
            brand matching
                ↓
            brand_stats GOLD layer
            """
        )

        cursor.close()

    except Exception as e:

        if conn:

            conn.rollback()

        logger.error(
            f"❌ GOLD PIPELINE FAILED: {str(e)}"
        )

        raise

    finally:

        if conn:

            conn.close()

            logger.info(
                "🔒 PostgreSQL connection closed"
            )

# ======================================
# MAIN
# ======================================

def run_pipeline():

    create_brand_table()

# ======================================
# ENTRYPOINT
# ======================================

if __name__ == "__main__":

    run_pipeline()