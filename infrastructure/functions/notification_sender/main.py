"""
CourtSync - Cloud Function: Notification Sender
Triggered by Pub/Sub 'notifications-queue' topic.
Sends WhatsApp messages via Twilio.
"""

import base64
import json
import logging
import os

import functions_framework
from twilio.rest import Client as TwilioClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

twilio_client = TwilioClient(
    os.getenv("TWILIO_ACCOUNT_SID"),
    os.getenv("TWILIO_AUTH_TOKEN"),
)


@functions_framework.cloud_event
def send_notification(cloud_event):
    """
    Triggered by: Pub/Sub topic 'notifications-queue'

    Flow:
    1. Decode notification from Pub/Sub
    2. Send WhatsApp message via Twilio
    3. Log delivery status
    """
    raw = cloud_event.data["message"].get("data", "")
    notification = json.loads(base64.b64decode(raw).decode("utf-8"))

    to_phone = notification.get("to")
    message_body = notification.get("message") or notification.get("text")

    if not to_phone or not message_body:
        logger.error(f"Invalid notification payload: {notification}")
        return {"status": "invalid_payload"}

    try:
        msg = twilio_client.messages.create(
            from_=f"whatsapp:{os.getenv('TWILIO_WHATSAPP_NUMBER')}",
            to=f"whatsapp:{to_phone}",
            body=message_body,
        )
        logger.info(f"Sent to {to_phone}: SID={msg.sid}")
        return {"status": "sent", "to": to_phone, "sid": msg.sid}

    except Exception as e:
        logger.error(f"Twilio error sending to {to_phone}: {e}")
        raise  # Cloud Functions will auto-retry on unhandled exception
