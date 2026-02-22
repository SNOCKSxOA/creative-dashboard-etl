# Creative Dashboard ETL

Täglicher Sync von Meta Ads Daten aus BigQuery nach Supabase.
Parst die SNOCKS Naming Convention in strukturierte Felder und aggregiert Performance-Metriken.

## Architektur

```
GitHub Push (main)
    │
    ▼  Cloud Build Trigger
    │  1. Tests
    │  2. Docker Build → Artifact Registry
    │  3. Deploy → Cloud Run
    │
    ▼  Cloud Run (täglich 06:00 UTC via Cloud Scheduler)
    │
    │  1. Fetch neue Daten aus BigQuery
    │  2. Parse Naming Convention (3 Schemas)
    │  3. Berechne KPIs (CTR, ROAS, CPC, etc.)
    │
    ▼
Supabase (PostgreSQL)
    ├── parsed_ad_dimensions (eine Zeile pro Ad)
    ├── daily_ad_metrics (eine Zeile pro Ad pro Tag)
    └── monthly_ad_summary (voraggregiert)
```

## Lokal entwickeln

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Tests ausführen
pytest tests/ -v

# Lokaler Run (mit GCP-Credentials)
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
cp .env.example .env  # Werte ausfüllen
python src/main.py
```

## GCP Setup (einmalig)

### 1. APIs aktivieren

```bash
gcloud services enable \
  cloudbuild.googleapis.com \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  secretmanager.googleapis.com
```

### 2. Artifact Registry Repository erstellen

```bash
gcloud artifacts repositories create creative-dashboard-etl \
  --repository-format=docker \
  --location=europe-west1
```

### 3. Service Account für Cloud Run erstellen

```bash
gcloud iam service-accounts create creative-etl-runner \
  --display-name="Creative Dashboard ETL Runner"

SA=creative-etl-runner@$PROJECT_ID.iam.gserviceaccount.com

# BigQuery lesen
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SA" --role="roles/bigquery.dataViewer"
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SA" --role="roles/bigquery.jobUser"

# Secret Manager lesen
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SA" --role="roles/secretmanager.secretAccessor"
```

### 4. Cloud Build Service Account berechtigen

```bash
CB_SA=$(gcloud projects describe $PROJECT_ID --format='value(projectNumber)')@cloudbuild.gserviceaccount.com

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$CB_SA" --role="roles/run.admin"
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$CB_SA" --role="roles/artifactregistry.writer"
gcloud iam service-accounts add-iam-policy-binding $SA \
  --member="serviceAccount:$CB_SA" --role="roles/iam.serviceAccountUser"
```

### 5. Secrets in Secret Manager anlegen

```bash
echo -n "project.dataset.table" | \
  gcloud secrets create BQ_TABLE --data-file=-

echo -n "https://xyz.supabase.co" | \
  gcloud secrets create SUPABASE_URL --data-file=-

echo -n "eyJ..." | \
  gcloud secrets create SUPABASE_SERVICE_ROLE_KEY --data-file=-
```

### 6. Cloud Build Trigger einrichten

In der GCP Console unter **Cloud Build → Triggers**:
- Repository verbinden (GitHub)
- Branch: `^main$`
- Konfiguration: `cloudbuild.yaml`
- Substitution hinzufügen: `_CLOUD_RUN_SA` = `creative-etl-runner@PROJECT_ID.iam.gserviceaccount.com`

Oder per CLI:
```bash
gcloud builds triggers create github \
  --name=creative-dashboard-etl \
  --repo-name=creative-dashboard-etl \
  --repo-owner=GITHUB_ORG \
  --branch-pattern=^main$ \
  --build-config=cloudbuild.yaml \
  --substitutions=_CLOUD_RUN_SA=creative-etl-runner@$PROJECT_ID.iam.gserviceaccount.com
```

### 7. Cloud Scheduler für täglichen Sync

```bash
SERVICE_URL=$(gcloud run services describe creative-dashboard-etl \
  --region europe-west1 --format 'value(status.url)')

gcloud scheduler jobs create http creative-dashboard-daily-sync \
  --location europe-west1 \
  --schedule "0 6 * * *" \
  --uri "$SERVICE_URL" \
  --http-method POST \
  --oidc-service-account-email creative-etl-runner@$PROJECT_ID.iam.gserviceaccount.com \
  --time-zone "Europe/Berlin"
```

### 8. Initialer Full Sync

```bash
curl -X POST $SERVICE_URL \
  -H "Authorization: Bearer $(gcloud auth print-identity-token)" \
  -H "Content-Type: application/json" \
  -d '{"full_sync": true}'
```

## TODO vor erstem Deploy

- [ ] Column Mapping in `src/bigquery_client.py` an echte Spaltennamen anpassen
- [ ] Supabase-Schema anlegen (SQL für alle 3 Tabellen + etl_sync_log)
- [ ] Parser mit echten Ad Names testen
- [ ] `_CLOUD_RUN_SA` in `cloudbuild.yaml` oder Trigger-Substitution eintragen
- [ ] GCP Setup (Schritte 1–6 oben) durchführen
