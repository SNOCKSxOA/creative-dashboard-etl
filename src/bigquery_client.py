"""BigQuery Client – Creative Dashboard ETL

Fetches creative-level Meta Ads data from BigQuery.
Table: snocks-analytics.marts_finance_euw3.ad_create_roas
"""

import logging
from google.cloud import bigquery

logger = logging.getLogger(__name__)

BQ_TABLE = "snocks-analytics.marts_finance_euw3.ad_create_roas"
META_CHANNELS = ["Meta Ads", "Facebook"]


def fetch_ads_data() -> tuple[list[dict], int]:
    """
    Fetch all Meta Ads creative data from BigQuery.
    Returns (rows as list of dicts, bytes scanned).
    """
    client = bigquery.Client()

    query = f"""
    SELECT
      company,
      extracted_CR_number,
      ad_names,
      channels,
      first_date,
      last_date,
      CAST(revenue AS FLOAT64) AS revenue,
      CAST(spend   AS FLOAT64) AS spend,
      CAST(roas    AS FLOAT64) AS roas
    FROM `{BQ_TABLE}`
    WHERE channels IN UNNEST(@channels)
    """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ArrayQueryParameter("channels", "STRING", META_CHANNELS)
        ]
    )

    logger.info(f"Querying {BQ_TABLE} for channels: {META_CHANNELS}")
    job = client.query(query, job_config=job_config)
    rows = [dict(row) for row in job.result()]
    bytes_scanned = job.total_bytes_processed or 0
    logger.info(f"Fetched {len(rows)} rows ({bytes_scanned:,} bytes scanned)")

    return rows, bytes_scanned


def test_connection() -> dict:
    """Test BigQuery connection and return table info."""
    try:
        client = bigquery.Client()
        table = client.get_table(BQ_TABLE)
        return {
            "table": BQ_TABLE,
            "num_rows": table.num_rows,
            "schema": [{"name": f.name, "type": f.field_type} for f in table.schema],
        }
    except Exception as e:
        return {"error": str(e)}
