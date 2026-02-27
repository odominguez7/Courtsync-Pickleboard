# CourtSync 🎾

> **AI-powered pickleball match coordinator — WhatsApp native**

Text *"3.5 doubles tomorrow 6pm"* and CourtSync finds you a game.

---

## What is CourtSync?

CourtSync is an AI agent that coordinates pickleball matches via WhatsApp. It solves the #1 problem in the sport's explosive growth: **intelligent match coordination at scale**.

- **19.8 million players** in the US (311% growth since 2020)
- **10,300 public courts** — supply/demand imbalance is severe
- **60%+ are 55+** — WhatsApp-native demographic
- **2,200 USAPA ambassadors** with 400+ player email lists each

Players send a natural-language message. CourtSync parses it with Gemini AI, matches players by DUPR skill rating (±0.5), coordinates schedules, recommends courts, and sends WhatsApp confirmations + calendar invites.

---

## How It Works

```
Player (WhatsApp)
    ↓ "3.5 doubles tomorrow 6pm"
Twilio WhatsApp API
    ↓
Cloud Function (webhook)
    ↓
Gemini 2.0 Flash
    ├─ Parse: skill level, format, time, location
    ├─ Match: find players with similar DUPR rating
    ├─ Notify: send invites to top 5 candidates
    └─ Coordinate: confirm when group is full
    ↓
Firestore (players, matches, courts)
    ↓
WhatsApp confirmations + Google Calendar invites
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Messaging | Twilio WhatsApp API → Meta Cloud API (Month 6+) |
| Backend (MVP) | Google Cloud Functions (Python 3.11) |
| Backend (Production) | Cloud Run + Cloud Functions + Cloud Run Jobs |
| AI | Gemini 2.0 Flash (Vertex AI) |
| Database | Firestore (NoSQL) |
| Analytics | BigQuery |
| Async Queue | Pub/Sub |
| Monitoring | Cloud Logging + Sentry + PostHog |
| Calendar | Google Calendar API |
| Cost (beta) | ~$3/month for 100 matches |

---

## Repository Structure

```
courtsync/
├── function/                    # Lean MVP — ship in 2 weeks
│   ├── main.py                  # Webhook entry point
│   ├── coordinator.py           # Core AI coordination logic
│   ├── matcher.py               # Skill + location matching engine
│   └── requirements.txt
│
├── config/
│   └── prompts.py               # Gemini system prompts + few-shot examples
│
├── infrastructure/              # Production-grade (Month 2+)
│   ├── api/                     # Cloud Run API Gateway (FastAPI)
│   │   ├── main.py
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   ├── functions/
│   │   ├── message_handler/     # Pub/Sub triggered message processor
│   │   ├── negotiation_engine/  # AI-powered schedule negotiation
│   │   └── notification_sender/ # Twilio WhatsApp dispatcher
│   └── jobs/
│       └── send_reminders/      # Hourly reminder job (Cloud Run Job)
│
├── scripts/
│   ├── setup_gcp.sh             # One-time GCP project bootstrapper
│   ├── deploy.sh                # Deploy lean or production mode
│   └── test_local.sh            # Local dev testing
│
├── docs/                        # Architecture & research documents
├── .env.yaml.example
├── .gitignore
└── README.md
```

---

## Quick Start — Lean MVP

### Prerequisites

- Google Cloud account with billing enabled
- Twilio account with WhatsApp Sandbox access
- Python 3.11+
- `gcloud` CLI installed and authenticated

### 1. GCP Setup

```bash
export PROJECT_ID="courtsync-mvp"
export BILLING_ACCOUNT="XXXXXX-XXXXXX-XXXXXX"
./scripts/setup_gcp.sh
```

### 2. Local Development

```bash
cd function
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Copy and fill in your credentials
cp ../.env.yaml.example ../.env.yaml
```

### 3. Deploy

```bash
# Lean MVP (recommended to start)
./scripts/deploy.sh lean

# Production infrastructure
./scripts/deploy.sh production
```

### 4. Connect Twilio Webhook

In your [Twilio Console](https://console.twilio.com) → Messaging → WhatsApp Sandbox:

Set the webhook URL to your deployed function URL:
```
https://REGION-PROJECT_ID.cloudfunctions.net/courtsync-coordinator
```

### 5. Test It

Open WhatsApp, message your Twilio sandbox number:
```
3.5 doubles tomorrow 6pm
```

---

## Database Schema

### `players` collection
```javascript
{
  "phone": "+12125551234",           // Document ID
  "profile": {
    "name": "Sam Chen",
    "dupr_rating": 3.5,
    "location": { "lat": 42.36, "lng": -71.05, "city": "Boston" }
  },
  "preferences": {
    "formats": ["doubles", "mixed_doubles"],
    "max_drive_minutes": 15
  },
  "stats": {
    "matches_played": 12,
    "reliability_score": 0.95        // Drops with no-shows
  },
  "active_match_id": null,
  "onboarding_complete": true
}
```

### `matches` collection
```javascript
{
  "match_id": "match_abc123",
  "status": "seeking_players|confirmed|completed|cancelled",
  "format": "doubles",
  "skill_range": { "min": 3.0, "max": 4.0, "target": 3.5 },
  "players": {
    "needed": 4,
    "confirmed": ["+1...", "+1..."],
    "pending": ["+1..."],
    "declined": []
  },
  "schedule": {
    "time_preference": "tomorrow 6pm",
    "duration_minutes": 90
  }
}
```

---

## Business Model

| Tier | Price | Matches/Month | Features |
|---|---|---|---|
| Free | $0 | 4 | Basic matching |
| Premium | $9.99/mo | Unlimited | Priority matching, analytics |
| Ambassador | $49/mo | Unlimited | League tools, bulk import, dashboard |

**Revenue at 10K users:** ~$50K–$100K ARR  
**Revenue at 100K users:** ~$500K–$1M ARR

---

## Cost Projections

| Scale | Users | Matches/mo | GCP Cost | Twilio Cost | Total |
|---|---|---|---|---|---|
| Beta | 100 | 400 | ~$3 | ~$40 | ~$43/mo |
| Growth | 10K | 40K | ~$150 | ~$4,000 | ~$4,150/mo |
| Scale | 100K | 400K | ~$800 | ~$1,200* | ~$2,000/mo |

*Meta Cloud API at scale replaces Twilio per-message cost.

---

## Roadmap

### Phase 1 — Beta (Weeks 1–4)
- [x] WhatsApp webhook + Twilio integration
- [x] Gemini AI intent parsing
- [x] Skill-based player matching
- [x] Match creation + player notification
- [x] YES/NO response handling
- [x] Match confirmation flow
- [ ] Google Calendar invite integration
- [ ] First 100 users via USAPA ambassador network

### Phase 2 — Growth (Months 2–3)
- [ ] Court database with geo search
- [ ] Negotiation engine (flexible scheduling)
- [ ] Reliability scoring (no-show tracking)
- [ ] PostHog analytics dashboard
- [ ] Premium tier subscription
- [ ] 1,000 users

### Phase 3 — Scale (Months 4–6)
- [ ] Migrate to Meta Cloud API
- [ ] Ambassador portal (web dashboard)
- [ ] League/tournament management
- [ ] DUPR API integration
- [ ] BigQuery analytics
- [ ] 10,000 users

---

## Research Foundation

This product is grounded in academic research:

- **Heo & Ryu (2023):** Social connection as primary retention driver
- **Lozano et al. (2025):** Match activity profiles for scheduling optimization
- **Prieto-Lage et al. (2024):** Performance analytics by skill zone
- **WHO-5 Wellbeing Index:** 3x/week play shows measurable wellbeing improvement
- **SFIA 2024:** 19.8M players, 311% growth, 44% YoY increase

See `/docs` for full research synthesis.

---

## Target Markets (Priority Order)

1. **Florida** — largest retirement + HOA base, strong pro scene
2. **California** — massive suburban base, heavy court conversions
3. **Texas** — fast-growing suburbs, rec sports culture
4. **Arizona** — Sunbelt retiree communities, high per-capita play
5. **Utah** — highest DUPR engagement, competitive depth

**Primary Persona: "Suburban Social Striver Sam"**
- Age 30–45, full-time job, time-limited
- Uses WhatsApp daily, not excited about another app
- Wants to maximize court time per hour of coordination

---

## Contributing

This is a private product in development. Contact the team for access.

---

*CourtSync — Coordination so good, you just have to show up and play.* 🎾
