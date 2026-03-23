<div align="center">

# CourtSync

**one text. four players. game on.**

The AI agent that coordinates pickleball matches through WhatsApp.
Text your skill level, preferred format, and when you want to play.
CourtSync handles the rest.

[![License: MIT](https://img.shields.io/badge/MIT-blue?style=for-the-badge)](LICENSE)
[![Python](https://img.shields.io/badge/Python_3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![GCP](https://img.shields.io/badge/Google_Cloud-4285F4?style=for-the-badge&logo=googlecloud&logoColor=white)](https://cloud.google.com)
[![WhatsApp](https://img.shields.io/badge/WhatsApp_Native-25D366?style=for-the-badge&logo=whatsapp&logoColor=white)](https://www.whatsapp.com)

</div>

---

## The problem

Pickleball is the fastest-growing sport in America. 19.8 million players. 311% growth since 2020. And the coordination is still done in group chats, spreadsheets, and Facebook threads.

Players waste more time finding a match than playing one.

- You text 15 people to fill a doubles game
- Half don't respond, half are the wrong skill level
- By the time you have 4 confirmed, the court slot is gone
- You do it again tomorrow

**CourtSync fixes this in one message.**

```
You:        "3.5 doubles tomorrow 6pm"
CourtSync:  "Found 3 players at the 3.0-4.0 level. Reaching out now."
CourtSync:  "Match confirmed! 4 players. Tomorrow 6pm. See you on the court."
```

No app to download. No account to create. Just WhatsApp -- the app 60% of pickleball players already use daily.

---

## How it works

```
┌────────────────────────────────────────────────────────────────┐
│                                                                │
│   Player sends WhatsApp message                                │
│   "3.5 doubles tomorrow 6pm"                                   │
│                                                                │
│   ┌──────────┐    ┌───────────────┐    ┌────────────────────┐  │
│   │  Twilio   │───▶│  Cloud Run    │───▶│  Pub/Sub Queue     │  │
│   │  Webhook  │    │  API Gateway  │    │  (async routing)   │  │
│   └──────────┘    └───────────────┘    └────────┬───────────┘  │
│                                                  │              │
│                   ┌──────────────────────────────┘              │
│                   ▼                                             │
│   ┌───────────────────────────────────────────────────────┐    │
│   │              Message Handler                          │    │
│   │                                                       │    │
│   │  ┌─────────────────┐    ┌──────────────────────────┐  │    │
│   │  │  Gemini 2.0     │    │  Skill Matcher           │  │    │
│   │  │  Flash          │    │                          │  │    │
│   │  │                 │    │  Composite score:        │  │    │
│   │  │  Parse intent   │    │  - Skill proximity (40%) │  │    │
│   │  │  Extract skill  │    │  - Distance (30%)        │  │    │
│   │  │  Extract time   │    │  - Reliability (20%)     │  │    │
│   │  │  Extract format │    │  - Engagement (10%)      │  │    │
│   │  └────────┬────────┘    └────────────┬─────────────┘  │    │
│   │           │                          │                │    │
│   │           └──────────┬───────────────┘                │    │
│   │                      ▼                                │    │
│   │           ┌──────────────────────┐                    │    │
│   │           │     Firestore        │                    │    │
│   │           │  players | matches   │                    │    │
│   │           └──────────────────────┘                    │    │
│   └───────────────────────────────────────────────────────┘    │
│                                                                │
│   ┌──────────────────┐    ┌──────────────────────────────┐    │
│   │  Notification     │    │  Reminder Job               │    │
│   │  Sender           │    │  (hourly via Cloud          │    │
│   │  (Pub/Sub → SMS)  │    │   Scheduler)                │    │
│   └──────────────────┘    └──────────────────────────────┘    │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

### The matching engine

When you say "3.5 doubles tomorrow 6pm", CourtSync:

1. **Parses** your message with Gemini 2.0 Flash -- extracts skill level, format, time preference, location
2. **Queries** all onboarded players within your DUPR range (default +/-0.5)
3. **Scores** each candidate on a 0-100 composite:

| Factor | Weight | How it works |
|---|---|---|
| Skill proximity | 40% | Closer DUPR rating = higher score |
| Geographic distance | 30% | Within 25km preferred |
| Reliability | 20% | Based on no-show history |
| Engagement | 10% | Recent match activity |

4. **Invites** the top 5 candidates via WhatsApp
5. **Tracks** YES/NO responses, moves players through the pipeline
6. **Confirms** once the group is full and notifies everyone

The entire flow happens over WhatsApp. No app. No login. No friction.

---

## The streak rules

CourtSync tracks reliability because nobody wants to organize a foursome and have someone ghost:

- **Reliability score** starts at 1.0 (100%)
- **No-shows** decrease your score -- you get matched less often
- **Consistent players** surface first in every search
- The system rewards people who show up

---

## Tech stack

| Layer | Technology | Why |
|---|---|---|
| **Messaging** | Twilio WhatsApp API | Instant sandbox access, production-ready |
| **AI** | Gemini 2.0 Flash (Vertex AI) | Fast intent parsing, JSON output, low cost |
| **API Gateway** | Cloud Run (FastAPI) | Auto-scaling, 10s timeout, signature verification |
| **Workers** | Cloud Functions (Gen2) | Event-driven, Pub/Sub triggered |
| **Database** | Firestore | NoSQL, real-time, zero ops |
| **Queue** | Google Cloud Pub/Sub | Async message routing between services |
| **Scheduler** | Cloud Scheduler | Hourly reminder jobs |
| **Geocoding** | geopy | Distance calculations for proximity matching |

**Cost at beta (100 users, 400 matches/month): ~$43/month.**

---

## Security

CourtSync handles phone numbers, locations, and message content. Security is not optional.

### What we enforce

| Protection | Implementation |
|---|---|
| **Webhook authentication** | Twilio signature verification (HMAC) -- always on in production |
| **Phone validation** | Regex `^\+?1?\d{10,15}$` on every input, rejects malformed numbers |
| **Rate limiting** | 20 messages/minute per phone number |
| **Prompt injection defense** | User input sanitized before AI prompt, phone numbers stripped from AI context |
| **Message limits** | 2000 chars inbound, 1600 chars outbound |
| **Log redaction** | Phone numbers masked in all logs (`+121****`) |
| **Secret management** | All credentials in GCP Secret Manager, never in code |
| **API docs hidden** | `/docs` and `/openapi.json` disabled in production |
| **Input sanitization** | Profile names truncated, message bodies length-limited |

### What we don't store

- No passwords (WhatsApp identity only)
- No payment data (not yet)
- No message content sent to third parties (Gemini runs on Vertex AI within GCP)

See [SECURITY.md](SECURITY.md) for our vulnerability disclosure policy.

---

## Quick start

### Prerequisites

- Google Cloud account with billing enabled
- Twilio account with WhatsApp Sandbox
- Python 3.11+
- `gcloud` CLI authenticated

### 1. Clone and configure

```bash
git clone https://github.com/odominguez7/Courtsync-Pickleboard.git
cd Courtsync-Pickleboard
cp .env.yaml.example .env.yaml   # fill in your credentials
```

### 2. Bootstrap GCP

```bash
export PROJECT_ID="your-project-id"
export BILLING_ACCOUNT="XXXXXX-XXXXXX-XXXXXX"
./scripts/setup_gcp.sh
```

This creates the project, enables APIs, sets up Firestore, Pub/Sub topics, and Secret Manager entries.

### 3. Deploy

```bash
# Lean MVP (single Cloud Function — ship in minutes)
./scripts/deploy.sh lean

# Production (Cloud Run + Cloud Functions + Scheduler)
./scripts/deploy.sh production
```

### 4. Connect Twilio

In [Twilio Console](https://console.twilio.com) > Messaging > WhatsApp Sandbox, set your webhook URL to the deployed function URL.

### 5. Test

Open WhatsApp, message your sandbox number:

```
3.5 doubles tomorrow 6pm
```

---

## Project structure

```
courtsync/
├── function/                         Lean MVP (single Cloud Function)
│   ├── main.py                       Webhook entry point
│   ├── coordinator.py                AI coordination engine (Gemini + Firestore)
│   ├── matcher.py                    Skill + location + reliability matching
│   └── requirements.txt
│
├── config/
│   └── prompts.py                    Gemini system prompts + few-shot examples
│
├── infrastructure/                   Production architecture
│   ├── api/                          Cloud Run API Gateway (FastAPI)
│   │   ├── main.py                   Webhook + signature verification + rate limiting
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   ├── functions/
│   │   ├── message_handler/          Pub/Sub → Coordinator → Notifications
│   │   ├── negotiation_engine/       AI schedule negotiation (future)
│   │   └── notification_sender/      Pub/Sub → Twilio WhatsApp
│   └── jobs/
│       └── send_reminders/           Hourly match reminder cron
│
├── scripts/
│   ├── setup_gcp.sh                  One-time GCP project bootstrap
│   ├── deploy.sh                     Deploy lean or production
│   └── test_local.sh                 Local development
│
├── SECURITY.md                       Vulnerability disclosure policy
├── .env.yaml.example                 Environment template
└── .gitignore
```

---

## Database schema

### `players` collection

```json
{
  "phone": "+12125551234",
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
    "reliability_score": 0.95
  },
  "active_match_id": null,
  "onboarding_complete": true
}
```

### `matches` collection

```json
{
  "match_id": "auto-generated",
  "status": "seeking_players | confirmed | completed | cancelled",
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

## The market

| Stat | Number | Source |
|---|---|---|
| US pickleball players | 19.8 million | SFIA 2024 |
| Growth since 2020 | 311% | SFIA 2024 |
| Players aged 55+ | 60%+ | USA Pickleball |
| Public courts | 10,300+ | Places2Play |
| USAPA ambassadors | 2,200 (400+ player lists each) | USA Pickleball |
| YoY growth rate | 44% | APP Tour |

**Primary persona: "Suburban Social Striver Sam"**
- 30-45, full-time job, limited free time
- Uses WhatsApp daily
- Doesn't want another app
- Wants to maximize court time per hour of coordination effort

**Target markets (priority):** Florida, California, Texas, Arizona, Utah

---

## Research foundation

Built on peer-reviewed research, not guesswork:

- **Heo & Ryu (2023):** Social connection is the primary retention driver in pickleball
- **Lozano et al. (2025):** Match activity profiles enable scheduling optimization
- **Prieto-Lage et al. (2024):** Performance analytics by court zone improve skill matching
- **WHO-5 Wellbeing Index:** 3x/week play shows measurable wellbeing improvement
- **SFIA 2024:** Market sizing and demographic data

See `md files MIT Libraries (R&D)/` for full research synthesis.

---

## Revenue model

| Tier | Price | Matches/month | Features |
|---|---|---|---|
| **Free** | $0 | 4 | Basic matching, WhatsApp coordination |
| **Premium** | $9.99/mo | Unlimited | Priority matching, analytics, calendar sync |
| **Ambassador** | $49/mo | Unlimited | League tools, bulk import, dashboard, branding |

| Scale | Users | Monthly cost | Projected ARR |
|---|---|---|---|
| Beta | 100 | ~$43 | -- |
| Growth | 10K | ~$4,150 | $50K-$100K |
| Scale | 100K | ~$2,000* | $500K-$1M |

*Meta Cloud API replaces Twilio per-message costs at scale.

---

## Roadmap

### Phase 1 -- Beta (Weeks 1-4)
- [x] WhatsApp webhook + Twilio integration
- [x] Gemini AI intent parsing
- [x] Skill-based player matching (DUPR +/-0.5)
- [x] Match creation + player notification
- [x] YES/NO response handling
- [x] Match confirmation flow
- [x] Security hardening (auth, rate limiting, input validation)
- [ ] Google Calendar invite integration
- [ ] First 100 users via USAPA ambassador network

### Phase 2 -- Growth (Months 2-3)
- [ ] Court database with geo search
- [ ] Negotiation engine (flexible scheduling)
- [ ] Reliability scoring (no-show tracking)
- [ ] Premium tier subscription
- [ ] PostHog analytics dashboard
- [ ] 1,000 users

### Phase 3 -- Scale (Months 4-6)
- [ ] Migrate to Meta Cloud API
- [ ] Ambassador portal (web dashboard)
- [ ] League and tournament management
- [ ] DUPR API integration
- [ ] BigQuery analytics pipeline
- [ ] 10,000 users

---

## The big objective

Pickleball doesn't need another app. It needs infrastructure.

19.8 million people play this sport and the coordination layer is still group chats and spreadsheets. That's not a feature gap -- it's a missing layer of the stack.

CourtSync is that layer. WhatsApp-native because that's where the players already are. AI-powered because matching by skill, location, reliability, and schedule is a problem that gets better with data, not worse. Open source because the best infrastructure is built in the open.

The goal is simple: **make it easier to play than to not play.** If finding a match takes one text message instead of fifteen, more people play. More people play, more people stay. More people stay, the sport grows.

We're not building a social network. We're not building a fitness app. We're building the coordination protocol for the fastest-growing sport in America.

**One text. Four players. Game on.**

---

<div align="center">

**Built by [Omar](https://github.com/odominguez7) -- MIT Sloan '26**

*Coordination so good, you just have to show up and play.*

</div>
