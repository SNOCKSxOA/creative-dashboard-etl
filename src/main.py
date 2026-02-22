"""
Creative Dashboard ETL – Main Entry Point

Cloud Run Service, täglich getriggert via Cloud Scheduler.
Fetcht Meta Ads Creative-Daten aus BigQuery, parst die SNOCKS Naming Convention,
und synchronisiert nach Supabase.
"""

import os
import logging

from flask import Flask, request, jsonify

from bigquery_client import fetch_ads_data
from parser import parse_ad_name
from supabase_client import (
    upsert_dimensions,
    upsert_creative_metrics,
    write_sync_log,
    update_sync_log,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

app = Flask(__name__)


def run_etl():
    """ETL: BigQuery → parse → Supabase."""
    sync_id = write_sync_log()
    logger.info(f"ETL gestartet – sync_id={sync_id}")

    try:
        # 1. Daten aus BigQuery laden
        rows, bytes_scanned = fetch_ads_data()
        logger.info(f"{len(rows)} Zeilen aus BigQuery geladen")

        if not rows:
            logger.info("Keine Daten zu verarbeiten")
            update_sync_log(sync_id, status="success", rows_processed=0, bq_bytes=bytes_scanned)
            return {"status": "success", "rows_processed": 0}

        # 2. Naming Convention parsen – Deduplizierung nach ad_name_raw
        dimensions_by_name = {}
        parse_error_count = 0

        for row in rows:
            ad_name = row.get("ad_names", "") or ""
            if ad_name in dimensions_by_name:
                continue  # Creative bereits geparst

            parsed = parse_ad_name(ad_name)
            parsed["ad_name_raw"] = ad_name

            if parsed.get("parse_errors"):
                parse_error_count += 1

            dimensions_by_name[ad_name] = parsed

        dimensions = list(dimensions_by_name.values())
        logger.info(f"{len(dimensions)} einzigartige Creatives geparst ({parse_error_count} mit Warnungen)")

        # Filter: nur CreativeTeam-Ads nach Supabase
        ALLOWED_SOURCES = {"CreativeTeam"}
        creative_team_names = {
            d["ad_name_raw"] for d in dimensions
            if d.get("creative_source") in ALLOWED_SOURCES
        }
        dimensions = [d for d in dimensions if d["ad_name_raw"] in creative_team_names]
        logger.info(f"{len(dimensions)} CreativeTeam-Creatives nach Filter")

        # 3. Metriken aufbereiten – deduplizieren nach (ad_name_raw, channels)
        metrics_by_key = {}
        for row in rows:
            if row.get("ad_names", "") not in creative_team_names:
                continue
            key = (row.get("ad_names", ""), row.get("channels", ""))
            metrics_by_key[key] = {
                "ad_name_raw": row.get("ad_names", ""),
                "company":     row.get("company", ""),
                "channels":    row.get("channels", ""),
                "first_date":  row.get("first_date"),
                "last_date":   row.get("last_date"),
                "revenue":     row.get("revenue"),
                "spend":       row.get("spend"),
                "roas":        row.get("roas"),
            }
        metrics = list(metrics_by_key.values())

        # 4. Nach Supabase schreiben
        dims_count = upsert_dimensions(dimensions)
        logger.info(f"{dims_count} Dimension-Zeilen upserted")

        metrics_count = upsert_creative_metrics(metrics)
        logger.info(f"{metrics_count} Metrik-Zeilen upserted")

        update_sync_log(
            sync_id,
            status="success",
            rows_processed=len(rows),
            bq_bytes=bytes_scanned,
        )
        logger.info(f"ETL abgeschlossen – {len(rows)} Zeilen verarbeitet")

        return {
            "status":               "success",
            "rows_processed":       len(rows),
            "dimensions_upserted":  dims_count,
            "metrics_upserted":     metrics_count,
            "parse_errors":         parse_error_count,
        }

    except Exception as e:
        logger.error(f"ETL fehlgeschlagen: {e}", exc_info=True)
        update_sync_log(sync_id, status="failed", error_message=str(e))
        raise


@app.route("/", methods=["POST"])
def handle_trigger():
    """HTTP-Endpoint für Cloud Scheduler."""
    try:
        result = run_etl()
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"status": "failed", "error": str(e)}), 500


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy"}), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
