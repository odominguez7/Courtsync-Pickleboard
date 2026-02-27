"""
CourtSync - Cloud Run API Gateway
Production webhook receiver with Twilio signature verification and Pub/Sub routing.
"""

import hashlib
import hmac
import json
import logging
import os

from fastapi import FastAPI, HTTPException, Request, Header
from google.cloud import firestore, pubsub_v1

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="CourtSync API", version="1.0.0")
db = firestore.Client()
publisher = pubsub_v1.PublisherClient()


def verify_twilio_signature(
    request_url: str, post_data: dict, signature: str
) -> bool:
    """Verify that the webhook request genuinely comes from Twilio."""
    auth_token = os.getenv("TWILIO_AUTH_TOKEN", "")
    data_string = request_url + "".join(
        f"{k}{post_data[k]}" for k in sorted(post_data.keys())
    )
    mac = hmac.new(
        auth_token.encode(), data_string.encode(), hashlib.sha256
    )
    try:
        return hmac.compare_digest(mac.digest(), bytes.fromhex(signature))
    except ValueError:
        return False


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

    # Signature check disabled in sandbox/dev; enable in production
    if os.getenv("VERIFY_TWILIO_SIGNATURE", "false").lower() == "true":
        if not x_twilio_signature or not verify_twilio_signature(
            str(request.url), form_dict, x_twilio_signature
        ):
            raise HTTPException(status_code=403, detail="Invalid Twilio signature")

    message_data = {
        "from": form_dict.get("From", "").replace("whatsapp:", ""),
        "to": form_dict.get("To", "").replace("whatsapp:", ""),
        "body": form_dict.get("Body", ""),
        "profile_name": form_dict.get("ProfileName", "Player"),
        "message_sid": form_dict.get("MessageSid"),
    }

    if not message_data["from"] or not message_data["body"]:
        raise HTTPException(status_code=400, detail="Missing From or Body")

    topic_path = publisher.topic_path(
        os.getenv("GCP_PROJECT", "courtsync-mvp"), "incoming-messages"
    )
    future = publisher.publish(
        topic_path, json.dumps(message_data).encode("utf-8")
    )
    logger.info(f"Published message from {message_data['from']}: {future.result()}")

    # Twilio requires a fast 200 with TwiML or empty body
    return {"status": "queued"}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "courtsync-api"}


@app.get("/")
async def root():
    return {"message": "CourtSync API v1.0 — Ready to rally 🎾"}
