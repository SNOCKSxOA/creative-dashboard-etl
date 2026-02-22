-- Creative Dashboard ETL – Supabase Schema
-- Ausführen im Supabase SQL Editor (Settings → SQL Editor)

-- =============================================================
-- 1. parsed_ad_dimensions
--    Eine Zeile pro einzigartigem Ad-Namen (geparste Naming Convention)
-- =============================================================
CREATE TABLE parsed_ad_dimensions (
  id               BIGSERIAL    PRIMARY KEY,
  ad_name_raw      TEXT         NOT NULL UNIQUE,

  -- Pflichtfelder (Positionen 1–7 der Naming Convention)
  schema_version   SMALLINT,
  product          TEXT,
  creative_id      TEXT,
  content_type     TEXT,
  adtype           TEXT,
  creative_cluster TEXT,
  in_ex            TEXT,
  creative_source  TEXT,
  is_ai            BOOLEAN      DEFAULT FALSE,

  -- Schema 1: Interne Creatives (Claudio, Katrin, CFC, ...)
  pl_eg_sp             TEXT,
  color                TEXT,
  element              TEXT,
  cr_kuerzel           TEXT,
  creative_tag         TEXT,
  format_video         TEXT,
  format_foto          TEXT,
  hook                 TEXT,
  text_kuerzel         TEXT,
  visual               TEXT,
  angle                TEXT,
  gender               TEXT,
  test_ids             TEXT,
  launch_year_week     TEXT,
  original_creative_id TEXT,
  additional_infos     TEXT,
  free_text            TEXT,
  ad_group_number      TEXT,

  -- Schema 2: Externe Agenturen (MT, SM, CreativeTeam, ...)
  color_freitext_pl TEXT,
  visual_ct         TEXT,
  creator_cluster   TEXT,
  text_edit         TEXT,
  text_align        TEXT,
  image_type        TEXT,
  copy_cluster      TEXT,
  zusatzfeld        TEXT,
  raw_suffix        TEXT,

  -- Metadaten
  parse_errors JSONB,
  parsed_at    TIMESTAMPTZ
);

-- =============================================================
-- 2. creative_metrics
--    Eine Zeile pro Ad-Name + Channel (BQ-Metriken)
-- =============================================================
CREATE TABLE creative_metrics (
  id          BIGSERIAL PRIMARY KEY,
  ad_name_raw TEXT      NOT NULL,
  company     TEXT,
  channels    TEXT,
  first_date  DATE,
  last_date   DATE,
  revenue     NUMERIC,
  spend       NUMERIC,
  roas        NUMERIC,
  synced_at   TIMESTAMPTZ,

  UNIQUE (ad_name_raw, channels)
);

-- =============================================================
-- 3. etl_sync_log
--    Eine Zeile pro ETL-Run
-- =============================================================
CREATE TABLE etl_sync_log (
  id                BIGSERIAL   PRIMARY KEY,
  sync_started_at   TIMESTAMPTZ NOT NULL,
  sync_completed_at TIMESTAMPTZ,
  status            TEXT        NOT NULL CHECK (status IN ('running', 'success', 'failed')),
  rows_processed    INTEGER     DEFAULT 0,
  bq_query_bytes    BIGINT      DEFAULT 0,
  error_message     TEXT
);
