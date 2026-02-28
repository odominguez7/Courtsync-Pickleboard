#!/bin/bash
# CourtSync - GCP Infrastructure Setup
# Run this FIRST to set up all cloud resources

set -e

PROJECT_ID="picklebot-488800"
REGION="us-central1"

echo "🚀 Setting up CourtSync infrastructure..."

# Create project (if it doesn't exist)
if ! gcloud projects describe $PROJECT_ID &>/dev/null; then
    echo "Creating GCP project: $PROJECT_ID"
    gcloud projects create $PROJECT_ID
fi

# Set project
gcloud config set project $PROJECT_ID

echo "📦 Enabling required APIs..."
gcloud services enable \
    run.googleapis.com \
    cloudfunctions.googleapis.com \
    firestore.googleapis.com \
    pubsub.googleapis.com \
    aiplatform.googleapis.com \
    secretmanager.googleapis.com \
    cloudbuild.googleapis.com

echo "🗄️  Creating Firestore database..."
gcloud firestore databases create --location=nam5 --type=firestore-native 2>/dev/null || echo "Firestore already exists"

echo "📨 Creating Pub/Sub topics..."
gcloud pubsub topics create events --project=$PROJECT_ID 2>/dev/null || echo "Topic 'events' already exists"

echo "🔐 Setting up Secret Manager..."
echo "Please enter your Twilio credentials:"
read -p "Twilio Account SID: " TWILIO_SID
read -p "Twilio Auth Token: " TWILIO_TOKEN
read -p "Twilio WhatsApp Number (e.g., +14155238886): " TWILIO_NUMBER

echo -n "$TWILIO_SID" | gcloud secrets create twilio-sid --data-file=- 2>/dev/null || \
    echo -n "$TWILIO_SID" | gcloud secrets versions add twilio-sid --data-file=-

echo -n "$TWILIO_TOKEN" | gcloud secrets create twilio-token --data-file=- 2>/dev/null || \
    echo -n "$TWILIO_TOKEN" | gcloud secrets versions add twilio-token --data-file=-

echo -n "$TWILIO_NUMBER" | gcloud secrets create twilio-number --data-file=- 2>/dev/null || \
    echo -n "$TWILIO_NUMBER" | gcloud secrets versions add twilio-number --data-file=-

echo "✅ Infrastructure setup complete!"
echo ""
echo "Next steps:"
echo "1. cd coordinator && deploy with: gcloud functions deploy courtsync-coordinator ..."
echo "2. cd api-gateway && deploy with: gcloud run deploy api-gateway ..."
echo "3. cd dashboard && deploy with: npm run build && gcloud run deploy dashboard ..."