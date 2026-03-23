"""
CourtSync - WhatsApp Webhook Entry Point
Receives WhatsApp messages via Twilio and routes to coordinator
"""

import functions_framework
from flask import Request
from coordinator import PickleballCoordinator
from twilio.twiml.messaging_response import MessagingResponse
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

coordinator = PickleballCoordinator()


@functions_framework.http
def whatsapp_webhook(request: Request):
    """
    Main webhook for WhatsApp messages via Twilio.

    Flow:
    1. Extract sender info and message from Twilio POST
    2. Route through PickleballCoordinator (AI + matching logic)
    3. Return TwiML response immediately (Twilio requires <10s)
    """

    if request.method == "GET":
        return "CourtSync webhook is live", 200

    from_number = request.form.get("From", "").replace("whatsapp:", "")
    message_body = request.form.get("Body", "").strip()
    from_name = request.form.get("ProfileName", "Player")

    if not from_number or not message_body:
        logger.warning("Missing From or Body in Twilio request")
        return "Bad Request", 400

    logger.info("Message from %s: %s...", from_number[:4] + "****" if len(from_number) > 4 else "****", message_body[:50])

    try:
        response_text = coordinator.process_message(
            player_phone=from_number,
            player_name=from_name,
            message=message_body,
        )
    except Exception as e:
        logger.error(f"Coordinator error: {e}", exc_info=True)
        response_text = (
            "Something went wrong on our end. Please try again in a moment!"
        )

    resp = MessagingResponse()
    resp.message(response_text)
    return str(resp), 200, {"Content-Type": "text/xml"}
