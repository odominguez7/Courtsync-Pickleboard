#!/bin/bash
# CourtSync - One-command deployment

set -e

PROJECT_ID="picklebot-488800"
REGION="us-central1"

echo "🚀 Deploying CourtSync to production..."

# Deploy Coordinator Function
echo "📦 Deploying Coordinator Agent..."
cd ../coordinator
gcloud functions deploy courtsync-coordinator \
    --gen2 \
    --runtime=python311 \
    --region=$REGION \
    --source=. \
    --entry-point=process_event \
    --trigger-topic=events \
    --set-env-vars GCP_PROJECT=$PROJECT_ID \
    --set-secrets TWILIO_ACCOUNT_SID=twilio-sid:latest,TWILIO_AUTH_TOKEN=twilio-token:latest,TWILIO_WHATSAPP_NUMBER=twilio-number:latest \
    --timeout=60s \
    --memory=1GB \
    --min-instances=1 \
    --max-instances=100

cd ..

# Deploy API Gateway
echo "🌐 Deploying API Gateway..."
cd api-gateway
gcloud run deploy api-gateway \
    --source=. \
    --region=$REGION \
    --allow-unauthenticated \
    --set-env-vars GCP_PROJECT=$PROJECT_ID \
    --set-secrets TWILIO_AUTH_TOKEN=twilio-token:latest \
    --memory=512Mi \
    --max-instances=10

# Get API Gateway URL
API_URL=$(gcloud run services describe api-gateway --region=$REGION --format='value(status.url)')
echo "✅ API Gateway deployed: $API_URL"
echo "⚠️  Set this as your Twilio webhook: $API_URL/webhooks/whatsapp"

cd ..

# Deploy Dashboard
echo "📊 Deploying Dashboard..."
cd dashboard
npm install
npm run build
gcloud run deploy dashboard \
    --source=. \
    --region=$REGION \
    --allow-unauthenticated \
    --set-env-vars NEXT_PUBLIC_PROJECT_ID=$PROJECT_ID

DASHBOARD_URL=$(gcloud run services describe dashboard --region=$REGION --format='value(status.url)')
echo "✅ Dashboard deployed: $DASHBOARD_URL"

cd ..

echo ""
echo "🎉 Deployment complete!"
echo ""
echo "Next steps:"
echo "1. Configure Twilio webhook: $API_URL/webhooks/whatsapp"
echo "2. View dashboard: $DASHBOARD_URL"
echo "3. Test by texting your Twilio WhatsApp number"