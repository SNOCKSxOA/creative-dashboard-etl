"""Supabase Client – Creative Dashboard ETL

Schreibt geparste Creative-Dimensions und BQ-Metriken nach Supabase.

Tabellen:
  - parsed_ad_dimensions  eine Zeile pro einzigartigem Ad-Namen (geparste Naming Convention)
  - creative_metrics       eine Zeile pro Ad-Name + Channel (spend, revenue, roas, dates)
  - etl_sync_log           eine Zeile pro ETL-Run
"""

import os
import logging
from datetime import datetime, timezone

from supabase import create_client, Client

logger = logging.getLogger(__name__)

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")

BATCH_SIZE = 500


def _get_client() -> Client:
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)


def _batch_upsert(client: Client, table: str, records: list[dict], on_conflict: str) -> int:
    total = 0
    for i in range(0, len(records), BATCH_SIZE):
        batch = records[i:i + BATCH_SIZE]
        client.table(table).upsert(batch, on_conflict=on_conflict).execute()
        total += len(batch)
        logger.debug(f"Batch {i // BATCH_SIZE + 1} → {table}: {len(batch)} records")
    return total


def upsert_dimensions(dimensions: list[dict]) -> int:
    """Upsert parsed ad dimensions. One row per unique ad_name_raw."""
    if not dimensions:
        return 0

    client = _get_client()
    now = datetime.now(timezone.utc).isoformat()

    records = []
    for d in dimensions:
        record = {
            "ad_name_raw":      d.get("ad_name_raw", ""),
            "schema_version":   d.get("schema_version", 3),
            "product":          d.get("product", ""),
            "creative_id":      d.get("creative_id", ""),
            "content_type":     d.get("content_type", ""),
            "adtype":           d.get("adtype", ""),
            "creative_cluster": d.get("creative_cluster", ""),
            "in_ex":            d.get("in_ex", ""),
            "creative_source":  d.get("creative_source", ""),
            "is_ai":            d.get("is_ai", False),
            "parsed_at":        now,
        }

        optional_fields = [
            "pl_eg_sp", "color", "element", "cr_kuerzel", "creative_tag",
            "format_video", "format_foto", "hook", "text_kuerzel", "visual",
            "angle", "gender", "test_ids", "launch_year_week",
            "original_creative_id", "additional_infos", "free_text",
            "ad_group_number", "color_freitext_pl", "visual_ct",
            "creator_cluster", "text_edit", "text_align", "image_type",
            "copy_cluster", "zusatzfeld", "raw_suffix",
        ]
        for field in optional_fields:
            val = d.get(field)
            if val is not None and val != "":
                record[field] = val

        if d.get("parse_errors"):
            record["parse_errors"] = d["parse_errors"]

        records.append(record)

    return _batch_upsert(client, "parsed_ad_dimensions", records, "ad_name_raw")


def upsert_creative_metrics(metrics: list[dict]) -> int:
    """Upsert creative-level metrics. One row per ad_name_raw + channels."""
    if not metrics:
        return 0

    client = _get_client()
    now = datetime.now(timezone.utc).isoformat()

    records = []
    for m in metrics:
        records.append({
            "ad_name_raw": m["ad_name_raw"],
            "company":     m.get("company", ""),
            "channels":    m.get("channels", ""),
            "first_date":  str(m["first_date"]) if m.get("first_date") else None,
            "last_date":   str(m["last_date"])  if m.get("last_date")  else None,
            "revenue":     float(m["revenue"])  if m.get("revenue")  is not None else None,
            "spend":       float(m["spend"])    if m.get("spend")    is not None else None,
            "roas":        float(m["roas"])     if m.get("roas")     is not None else None,
            "synced_at":   now,
        })

    return _batch_upsert(client, "creative_metrics", records, "ad_name_raw,channels")


def write_sync_log() -> int:
    client = _get_client()
    result = (
        client.table("etl_sync_log")
        .insert({"sync_started_at": datetime.now(timezone.utc).isoformat(), "status": "running"})
        .execute()
    )
    return result.data[0]["id"]


def update_sync_log(sync_id: int, status: str, rows_processed: int = 0,
                    error_message: str = None, bq_bytes: int = 0):
    client = _get_client()
    data = {
        "status":         status,
        "rows_processed": rows_processed,
        "bq_query_bytes": bq_bytes,
    }
    if status in ("success", "failed"):
        data["sync_completed_at"] = datetime.now(timezone.utc).isoformat()
    if error_message:
        data["error_message"] = error_message
    client.table("etl_sync_log").update(data).eq("id", sync_id).execute()
