#!/bin/bash
# CourtSync - GCP Project Setup Script
# Run once to bootstrap your Google Cloud project

set -euo pipefail

export PROJECT_ID="${PROJECT_ID:-courtsync-mvp}"
export REGION="${REGION:-us-central1}"
export BILLING_ACCOUNT="${BILLING_ACCOUNT:-}"  # Set before running

echo "========================================="
echo " CourtSync GCP Setup"
echo " Project: $PROJECT_ID | Region: $REGION"
echo "========================================="

# 1. Create and configure project
gcloud projects create "$PROJECT_ID" --name="CourtSync MVP" || true
gcloud config set project "$PROJECT_ID"

# 2. Link billing (required for Cloud Functions + Firestore)
if [ -n "$BILLING_ACCOUNT" ]; then
  gcloud beta billing projects link "$PROJECT_ID" \
    --billing-account="$BILLING_ACCOUNT"
else
  echo "⚠️  BILLING_ACCOUNT not set. Set it and re-run or link billing manually."
fi

# 3. Enable required APIs
echo "Enabling APIs..."
gcloud services enable \
  cloudfunctions.googleapis.com \
  run.googleapis.com \
  firestore.googleapis.com \
  aiplatform.googleapis.com \
  pubsub.googleapis.com \
  secretmanager.googleapis.com \
  cloudscheduler.googleapis.com \
  cloudbuild.googleapis.com \
  containerregistry.googleapis.com \
  calendar-json.googleapis.com \
  maps-backend.googleapis.com

# 4. Create Firestore database
echo "Creating Firestore database..."
gcloud firestore databases create --location=nam5 || true

# 5. Create Pub/Sub topics
echo "Creating Pub/Sub topics..."
gcloud pubsub topics create incoming-messages || true
gcloud pubsub topics create match-updates || true
gcloud pubsub topics create notifications-queue || true

# 6. Store Twilio credentials in Secret Manager
echo ""
echo "Storing secrets in Secret Manager..."
echo "Enter your Twilio Account SID:"
read -r TWILIO_ACCOUNT_SID
echo -n "$TWILIO_ACCOUNT_SID" | gcloud secrets create twilio-sid --data-file=- || \
  echo -n "$TWILIO_ACCOUNT_SID" | gcloud secrets versions add twilio-sid --data-file=-

echo "Enter your Twilio Auth Token:"
read -r -s TWILIO_AUTH_TOKEN
echo -n "$TWILIO_AUTH_TOKEN" | gcloud secrets create twilio-auth --data-file=- || \
  echo -n "$TWILIO_AUTH_TOKEN" | gcloud secrets versions add twilio-auth --data-file=-

echo "Enter your Twilio WhatsApp Number (e.g. +14155238886):"
read -r TWILIO_WHATSAPP_NUMBER
echo -n "$TWILIO_WHATSAPP_NUMBER" | gcloud secrets create twilio-number --data-file=- || \
  echo -n "$TWILIO_WHATSAPP_NUMBER" | gcloud secrets versions add twilio-number --data-file=-

# 7. Create service account for scheduler
gcloud iam service-accounts create courtsync-scheduler \
  --display-name="CourtSync Scheduler" || true

gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:courtsync-scheduler@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/run.invoker"

echo ""
echo "✅ GCP setup complete!"
echo "Next: run ./scripts/deploy.sh to deploy all services."
