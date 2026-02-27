#!/bin/bash
# CourtSync - Full Deployment Script
# Deploys all Cloud Functions, Cloud Run API, and scheduled jobs

set -euo pipefail

export PROJECT_ID="${PROJECT_ID:-courtsync-mvp}"
export REGION="${REGION:-us-central1}"

echo "========================================="
echo " CourtSync Deployment"
echo " Project: $PROJECT_ID | Region: $REGION"
echo "========================================="

# ── Option A: Lean MVP (single Cloud Function) ────────────────────────────────
deploy_lean_mvp() {
  echo ""
  echo "--- Deploying Lean MVP Function ---"
  gcloud functions deploy courtsync-coordinator \
    --gen2 \
    --runtime python311 \
    --region "$REGION" \
    --source ./function \
    --entry-point whatsapp_webhook \
    --trigger-http \
    --allow-unauthenticated \
    --set-env-vars GCP_PROJECT="$PROJECT_ID" \
    --set-secrets \
      TWILIO_ACCOUNT_SID=twilio-sid:latest,\
      TWILIO_AUTH_TOKEN=twilio-auth:latest,\
      TWILIO_WHATSAPP_NUMBER=twilio-number:latest \
    --timeout 30s \
    --memory 512MB

  echo "✅ Lean MVP deployed."
  echo "Webhook URL:"
  gcloud functions describe courtsync-coordinator \
    --region "$REGION" \
    --format "value(serviceConfig.uri)"
}

# ── Option B: Production Infrastructure ──────────────────────────────────────
deploy_production() {
  echo ""
  echo "--- Deploying Cloud Run API Gateway ---"
  gcloud run deploy courtsync-api \
    --source ./infrastructure/api \
    --region "$REGION" \
    --allow-unauthenticated \
    --max-instances 10 \
    --memory 512Mi \
    --timeout 10s \
    --set-env-vars GCP_PROJECT="$PROJECT_ID" \
    --set-secrets TWILIO_AUTH_TOKEN=twilio-auth:latest

  echo ""
  echo "--- Deploying Message Handler Function ---"
  gcloud functions deploy message-handler \
    --gen2 \
    --runtime python311 \
    --region "$REGION" \
    --source ./infrastructure/functions/message_handler \
    --entry-point handle_message \
    --trigger-topic incoming-messages \
    --set-env-vars GCP_PROJECT="$PROJECT_ID" \
    --set-secrets \
      TWILIO_ACCOUNT_SID=twilio-sid:latest,\
      TWILIO_AUTH_TOKEN=twilio-auth:latest,\
      TWILIO_WHATSAPP_NUMBER=twilio-number:latest \
    --timeout 60s \
    --memory 512MB

  echo ""
  echo "--- Deploying Negotiation Engine Function ---"
  gcloud functions deploy negotiation-engine \
    --gen2 \
    --runtime python311 \
    --region "$REGION" \
    --source ./infrastructure/functions/negotiation_engine \
    --entry-point run_negotiation \
    --trigger-topic match-updates \
    --set-env-vars GCP_PROJECT="$PROJECT_ID" \
    --timeout 60s

  echo ""
  echo "--- Deploying Notification Sender Function ---"
  gcloud functions deploy notification-sender \
    --gen2 \
    --runtime python311 \
    --region "$REGION" \
    --source ./infrastructure/functions/notification_sender \
    --entry-point send_notification \
    --trigger-topic notifications-queue \
    --set-secrets \
      TWILIO_ACCOUNT_SID=twilio-sid:latest,\
      TWILIO_AUTH_TOKEN=twilio-auth:latest,\
      TWILIO_WHATSAPP_NUMBER=twilio-number:latest \
    --timeout 30s

  echo ""
  echo "--- Deploying Reminder Job ---"
  gcloud builds submit \
    --tag "gcr.io/${PROJECT_ID}/send-reminders" \
    ./infrastructure/jobs/send_reminders

  gcloud run jobs create send-reminders \
    --image "gcr.io/${PROJECT_ID}/send-reminders" \
    --region "$REGION" \
    --task-timeout 10m \
    --set-env-vars GCP_PROJECT="$PROJECT_ID" || \
  gcloud run jobs update send-reminders \
    --image "gcr.io/${PROJECT_ID}/send-reminders" \
    --region "$REGION"

  gcloud scheduler jobs create http send-reminders-trigger \
    --location "$REGION" \
    --schedule "0 * * * *" \
    --uri "https://${REGION}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${PROJECT_ID}/jobs/send-reminders:run" \
    --http-method POST \
    --oauth-service-account-email "courtsync-scheduler@${PROJECT_ID}.iam.gserviceaccount.com" || true

  echo "✅ Production infrastructure deployed."
}

# ── Entry Point ───────────────────────────────────────────────────────────────
MODE="${1:-lean}"

case "$MODE" in
  lean)
    deploy_lean_mvp
    ;;
  production)
    deploy_production
    ;;
  *)
    echo "Usage: ./scripts/deploy.sh [lean|production]"
    exit 1
    ;;
esac

echo ""
echo "🎾 CourtSync is live! Don't forget to set your Twilio webhook URL."
