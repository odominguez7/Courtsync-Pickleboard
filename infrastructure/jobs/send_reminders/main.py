"""
CourtSync - Cloud Run Job: Send Reminders
Runs hourly via Cloud Scheduler.
Sends 2-hour-before reminders to all players with confirmed matches.
"""

import json
import logging
import os
from datetime import datetime, timedelta, timezone

from google.cloud import firestore, pubsub_v1

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

db = firestore.Client()
publisher = pubsub_v1.PublisherClient()


def main():
    """Check for upcoming matches and send reminders."""
    now = datetime.now(timezone.utc)
    two_hours_later = now + timedelta(hours=2)

    logger.info(f"Scanning matches between {now.isoformat()} and {two_hours_later.isoformat()}")

    matches = (
        db.collection("matches")
        .where("status", "==", "confirmed")
        .where("scheduled_at", ">=", now)
        .where("scheduled_at", "<=", two_hours_later)
        .stream()
    )

    reminders_sent = 0

    for match_doc in matches:
        match = match_doc.to_dict()

        if match.get("reminder_sent"):
            logger.info(f"Reminder already sent for {match.get('match_id')}")
            continue

        for player_phone in match.get("players", {}).get("confirmed", []):
            _queue_reminder(player_phone, match)
            reminders_sent += 1

        match_doc.reference.update(
            {
                "reminder_sent": True,
                "reminder_sent_at": firestore.SERVER_TIMESTAMP,
            }
        )

    logger.info(f"Queued {reminders_sent} reminders")
    return {"reminders_sent": reminders_sent}


def _queue_reminder(player_phone: str, match: dict):
    """Push a reminder notification to the notifications-queue Pub/Sub topic."""
    scheduled = match.get("scheduled_at")
    time_str = scheduled.strftime("%I:%M %p") if scheduled else "soon"

    location = match.get("details", {}).get("where") or match.get("court", {}).get(
        "name", "your court"
    )
    fmt = match.get("format", "doubles").replace("_", " ").title()

    message = (
        f"⏰ Reminder: Match in ~2 hours!\n\n"
        f"Format: {fmt}\n"
        f"Time: {time_str}\n"
        f"Location: {location}\n\n"
        f"See you on the court! 🎾"
    )

    topic_path = publisher.topic_path(
        os.getenv("GCP_PROJECT", "courtsync-mvp"), "notifications-queue"
    )
    publisher.publish(
        topic_path,
        json.dumps({"to": player_phone, "message": message}).encode("utf-8"),
    )


if __name__ == "__main__":
    main()
