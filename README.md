# CourtSync MVP 🎾

AI-powered pickleball match coordinator via WhatsApp.

## Architecture

- **Coordinator**: Single intelligent agent powered by Gemini 2.0 Flash
- **API Gateway**: FastAPI webhook receiver 
- **Dashboard**: Next.js real-time monitoring
- **Infrastructure**: Google Cloud (Functions, Firestore, Pub/Sub)

## Quick Start

```bash
# 1. Setup infrastructure
cd scripts
./setup-gcp.sh

# 2. Deploy everything
./deploy.sh

# 3. Configure Twilio webhook
# Set webhook URL from deploy output
```

## Project Structure

```
courtsync-mvp/
├── coordinator/         # AI agent (Cloud Function)
├── api-gateway/        # Webhook receiver (Cloud Run)
├── dashboard/          # Real-time UI (Cloud Run)
└── scripts/           # Deployment automation
```

## Testing

Send WhatsApp message to your Twilio number:
- "Need doubles 3.5 level tomorrow 6pm"
- "YES" / "NO" to confirm
- "3.5" to set skill level

## Status

🚧 Under active development for E14 Hackathon