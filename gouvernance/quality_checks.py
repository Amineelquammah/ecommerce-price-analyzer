# governance/quality_checks.py

from pyspark.sql.functions import col
from governance.monitoring import logger


def check_empty_dataframe(df, dataset_name="dataset"):
    """
    Ensure dataframe is not empty.
    """

    count = df.count()

    logger.info(f"{dataset_name} row count: {count}")

    if count == 0:
        logger.error(f"{dataset_name} is EMPTY")

        raise Exception(f"{dataset_name} is EMPTY")


def check_nulls(df, columns, dataset_name="dataset"):
    """
    Check null values for important columns.
    """

    for column in columns:

        null_count = df.filter(
            col(column).isNull()
        ).count()

        logger.info(
            f"{dataset_name}.{column} -> {null_count} nulls"
        )

        if null_count > 0:
            logger.warning(
                f"{dataset_name}.{column} contains {null_count} null values"
            )


def check_duplicates(df, subset_columns, dataset_name="dataset"):
    """
    Detect duplicated rows.
    """

    total_rows = df.count()

    distinct_rows = df.dropDuplicates(subset_columns).count()

    duplicates = total_rows - distinct_rows

    logger.info(
        f"{dataset_name} duplicates: {duplicates}"
    )

    if duplicates > 0:
        logger.warning(
            f"{dataset_name} contains {duplicates} duplicates"
        )


def check_price_quality(df, price_column="price"):
    """
    Validate product prices.
    """

    invalid_prices = df.filter(
        (col(price_column) <= 0) |
        col(price_column).isNull()
    ).count()

    logger.info(
        f"Invalid prices detected: {invalid_prices}"
    )

    if invalid_prices > 0:
        logger.warning(
            f"{invalid_prices} invalid prices found"
        )