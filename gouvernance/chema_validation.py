# governance/schema_validation.py

from governance.monitoring import logger


def validate_columns(df, required_columns, dataset_name="dataset"):
    """
    Validate required schema columns.
    """

    missing_columns = []

    for column in required_columns:
        if column not in df.columns:
            missing_columns.append(column)

    if missing_columns:
        logger.error(
            f"{dataset_name} missing columns: {missing_columns}"
        )

        raise Exception(
            f"{dataset_name} missing columns: {missing_columns}"
        )

    logger.info(
        f"{dataset_name} schema validation passed"
    )