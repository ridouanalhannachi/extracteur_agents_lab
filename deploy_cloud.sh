#!/usr/bin/env bash
set -euo pipefail

SERVICE_NAME="${SERVICE_NAME:-extracteur-edt-rh}"
REGION="${REGION:-europe-west1}"

if [[ -z "${GOOGLE_CLOUD_PROJECT:-}" ]]; then
  echo "Définissez GOOGLE_CLOUD_PROJECT avant de lancer ce script."
  echo "Exemple: export GOOGLE_CLOUD_PROJECT=mon-projet"
  exit 1
fi

if [[ ! -f data/gdrive/token.json ]]; then
  echo "data/gdrive/token.json est absent. Connectez d'abord Google Drive en local."
  exit 1
fi

if [[ -z "${APP_PASSWORD:-}" ]]; then
  echo "Définissez APP_PASSWORD dans ce terminal avant le premier déploiement."
  exit 1
fi

gcloud config set project "$GOOGLE_CLOUD_PROJECT"
gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com secretmanager.googleapis.com drive.googleapis.com

if gcloud secrets describe gdrive-token >/dev/null 2>&1; then
  gcloud secrets versions add gdrive-token --data-file=data/gdrive/token.json
else
  gcloud secrets create gdrive-token --replication-policy=automatic --data-file=data/gdrive/token.json
fi

printf '%s' "$APP_PASSWORD" > /tmp/edt-app-password.txt
if gcloud secrets describe edt-app-password >/dev/null 2>&1; then
  gcloud secrets versions add edt-app-password --data-file=/tmp/edt-app-password.txt
else
  gcloud secrets create edt-app-password --replication-policy=automatic --data-file=/tmp/edt-app-password.txt
fi
rm -f /tmp/edt-app-password.txt

PROJECT_NUMBER="$(gcloud projects describe "$GOOGLE_CLOUD_PROJECT" --format='value(projectNumber)')"
RUNTIME_SA="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"
gcloud secrets add-iam-policy-binding gdrive-token --member="serviceAccount:${RUNTIME_SA}" --role="roles/secretmanager.secretAccessor" >/dev/null
gcloud secrets add-iam-policy-binding edt-app-password --member="serviceAccount:${RUNTIME_SA}" --role="roles/secretmanager.secretAccessor" >/dev/null

gcloud run deploy "$SERVICE_NAME" \
  --source . \
  --region "$REGION" \
  --allow-unauthenticated \
  --set-env-vars APP_MODE=cloud,APP_DATA_DIR=/tmp/extracteur-edt-rh \
  --set-secrets GDRIVE_TOKEN_JSON=gdrive-token:latest,APP_PASSWORD=edt-app-password:latest \
  --max-instances 1 \
  --min-instances 0 \
  --concurrency 1 \
  --memory 1Gi \
  --cpu 1

echo "Déploiement terminé. L'URL Cloud Run est affichée ci-dessus."
