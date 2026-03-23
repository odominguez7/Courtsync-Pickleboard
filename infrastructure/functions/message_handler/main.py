"""
CourtSync - Cloud Function: Message Handler
Triggered by Pub/Sub 'incoming-messages' topic.
Processes inbound WhatsApp messages through the coordinator.
"""

import json
import logging

import functions_framework
from google.cloud import firestore, pubsub_v1

from coordinator import CourtSyncCoordinator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

db = firestore.Client()
publisher = pubsub_v1.PublisherClient()
coordinator = CourtSyncCoordinator()


@functions_framework.cloud_event
def handle_message(cloud_event):
    """
    Triggered by: Pub/Sub topic 'incoming-messages'

    Flow:
    1. Parse message from Pub/Sub
    2. Get/create user profile
    3. Route through coordinator
    4. Publish response notifications to queue
    """
    import base64

    raw = cloud_event.data["message"].get("data", "")
    message_data = json.loads(base64.b64decode(raw).decode("utf-8"))

    user_phone = message_data["from"]
    message_body = message_data["body"]
    profile_name = message_data.get("profile_name", "Player")

    redacted = user_phone[:4] + "****" if len(user_phone) > 4 else "****"
    logger.info("Processing message from %s: %s", redacted, message_body[:50])

    result = coordinator.process_message(
        player_phone=user_phone,
        player_name=profile_name,
        message=message_body,
    )

    # Log to Firestore
    db.collection("messages").add(
        {
            "from": user_phone,
            "body": message_body,
            "intent": result.get("intent"),
            "timestamp": firestore.SERVER_TIMESTAMP,
        }
    )

    # Queue outbound notifications
    if result.get("notifications"):
        import os

        topic_path = publisher.topic_path(
            os.getenv("GCP_PROJECT", "courtsync-mvp"), "notifications-queue"
        )
        for notification in result["notifications"]:
            publisher.publish(
                topic_path, json.dumps(notification).encode("utf-8")
            )

    return {"status": "processed"}
