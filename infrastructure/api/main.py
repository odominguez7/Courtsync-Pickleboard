"""
CourtSync - Cloud Run API Gateway
Production webhook receiver with Twilio signature verification and Pub/Sub routing.
"""

import json
import logging
import os
import re
import time

from fastapi import FastAPI, HTTPException, Request, Header
from google.cloud import firestore, pubsub_v1
from twilio.request_validator import RequestValidator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_IS_PROD = bool(os.getenv("K_SERVICE"))  # Set by Cloud Run

app = FastAPI(
    title="CourtSync API",
    version="1.0.0",
    docs_url=None if _IS_PROD else "/docs",
    redoc_url=None if _IS_PROD else "/redoc",
    openapi_url=None if _IS_PROD else "/openapi.json",
)
db = firestore.Client()
publisher = pubsub_v1.PublisherClient()

# Twilio signature verification — uses official SDK validator
_twilio_validator = None


def _get_twilio_validator() -> RequestValidator:
    global _twilio_validator
    if _twilio_validator is None:
        auth_token = os.getenv("TWILIO_AUTH_TOKEN", "")
        if not auth_token and _IS_PROD:
            raise RuntimeError("TWILIO_AUTH_TOKEN must be set in production")
        _twilio_validator = RequestValidator(auth_token)
    return _twilio_validator


# Phone number validation
_PHONE_RE = re.compile(r"^\+?1?\d{10,15}$")


def _validate_phone(phone: str) -> str:
    """Validate and normalize phone number. Raises HTTPException if invalid."""
    cleaned = phone.replace("whatsapp:", "").strip()
    if not _PHONE_RE.match(cleaned):
        raise HTTPException(status_code=400, detail="Invalid phone number")
    return cleaned


# Rate limiting: per-phone, max 20 messages per minute
_rate_limits: dict[str, list[float]] = {}
_RATE_LIMIT = 20
_RATE_WINDOW = 60


def _check_rate_limit(phone: str):
    now = time.time()
    cutoff = now - _RATE_WINDOW
    hits = [t for t in _rate_limits.get(phone, []) if t > cutoff]
    if len(hits) >= _RATE_LIMIT:
        _rate_limits[phone] = hits
        raise HTTPException(status_code=429, detail="Too many messages. Slow down.")
    hits.append(now)
    _rate_limits[phone] = hits
    # Prune old entries
    if len(_rate_limits) > 5000:
        stale = [k for k, v in _rate_limits.items() if not v or v[-1] < cutoff]
        for k in stale:
            del _rate_limits[k]


@app.post("/webhooks/whatsapp")
async def whatsapp_webhook(
    request: Request,
    x_twilio_signature: str = Header(None),
):
    """
    Main WhatsApp webhook. Validates Twilio signature then queues
    the message to Pub/Sub for async processing.
    """
    form_data = await request.form()
    form_dict = dict(form_data)

    # Twilio signature verification — always on in production
    if _IS_PROD:
        validator = _get_twilio_validator()
        if not x_twilio_signature or not validator.validate(
            str(request.url), form_dict, x_twilio_signature
        ):
            logger.warning("Rejected request with invalid Twilio signature")
            raise HTTPException(status_code=403, detail="Invalid signature")

    # Validate and normalize phone
    raw_from = form_dict.get("From", "")
    from_phone = _validate_phone(raw_from)

    body = (form_dict.get("Body") or "").strip()
    if not body:
        raise HTTPException(status_code=400, detail="Missing message body")

    # Enforce message length limit
    if len(body) > 2000:
        body = body[:2000]

    # Rate limit per phone
    _check_rate_limit(from_phone)

    message_data = {
        "from": from_phone,
        "to": _validate_phone(form_dict.get("To", "")),
        "body": body,
        "profile_name": (form_dict.get("ProfileName") or "Player")[:100],
        "message_sid": form_dict.get("MessageSid"),
    }

    topic_path = publisher.topic_path(
        os.getenv("GCP_PROJECT", "courtsync-mvp"), "incoming-messages"
    )
    future = publisher.publish(
        topic_path, json.dumps(message_data).encode("utf-8")
    )
    logger.info("Published message from %s: %s", from_phone[:4] + "****", future.result())

    # Twilio requires a fast 200 with TwiML or empty body
    return {"status": "queued"}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "courtsync-api"}


@app.get("/")
async def root():
    return {"message": "CourtSync API v1.0"}
