"""
CourtSync - Cloud Function: Negotiation Engine
Triggered by Pub/Sub 'match-updates' topic.
Uses Gemini AI to find optimal match times and nudge non-responders.
"""

import base64
import json
import logging
import os

import functions_framework
from google.cloud import firestore, pubsub_v1
from vertexai.generative_models import GenerativeModel
import vertexai

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

db = firestore.Client()
publisher = pubsub_v1.PublisherClient()
vertexai.init(project=os.getenv("GCP_PROJECT", "courtsync-mvp"))
model = GenerativeModel("gemini-2.0-flash-exp")


@functions_framework.cloud_event
def run_negotiation(cloud_event):
    """
    Triggered by: Pub/Sub topic 'match-updates'

    Flow:
    1. Get match state from Firestore
    2. Analyze all availability responses
    3. Find optimal time intersection
    4. Generate personalized nudges for non-responders
    5. Update match state and queue notifications
    """
    raw = cloud_event.data["message"].get("data", "")
    match_id = base64.b64decode(raw).decode("utf-8").strip()

    logger.info(f"Running negotiation for match {match_id}")

    match_ref = db.collection("matches").document(match_id)
    match = match_ref.get().to_dict()

    if not match:
        logger.error(f"Match {match_id} not found")
        return {"status": "not_found"}

    context = _build_negotiation_context(match)

    prompt = f"""
You are coordinating a pickleball match. Analyze the current state and determine the best next action.

Match context:
{json.dumps(context, indent=2)}

Your tasks:
1. Find the best time that works for most players
2. Generate personalized messages for pending players using social proof and urgency
3. If enough players confirmed, propose finalizing the match

Return JSON only:
{{
  "optimal_time": "ISO datetime or null",
  "match_ready": false,
  "next_actions": ["list of actions"],
  "messages": [
    {{"to": "+1234567890", "text": "personalized nudge"}}
  ]
}}
"""

    response = model.generate_content(
        prompt,
        generation_config={"temperature": 0.4, "max_output_tokens": 800},
    )

    json_str = response.text.strip()
    if "```json" in json_str:
        json_str = json_str.split("```json")[1].split("```")[0]

    try:
        decision = json.loads(json_str)
    except json.JSONDecodeError:
        logger.error(f"Failed to parse negotiation response: {json_str[:200]}")
        return {"status": "parse_error"}

    # Update match state
    update_data = {
        "negotiation.rounds": firestore.Increment(1),
        "ai_decision": decision,
        "updated_at": firestore.SERVER_TIMESTAMP,
    }
    if decision.get("optimal_time"):
        update_data["negotiation.optimal_time"] = decision["optimal_time"]

    match_ref.update(update_data)

    # Queue outbound messages
    if decision.get("messages"):
        topic_path = publisher.topic_path(
            os.getenv("GCP_PROJECT", "courtsync-mvp"), "notifications-queue"
        )
        for msg in decision["messages"]:
            publisher.publish(
                topic_path, json.dumps(msg).encode("utf-8")
            )

    logger.info(
        f"Negotiation round complete. Optimal time: {decision.get('optimal_time')}"
    )
    return {"status": "negotiation_complete", "decision": decision}


def _build_negotiation_context(match: dict) -> dict:
    return {
        "match_id": match.get("match_id"),
        "format": match.get("details", {}).get("format", match.get("format")),
        "location": match.get("details", {}).get("where"),
        "players_needed": match.get("players", {}).get("needed"),
        "players_confirmed": match.get("players", {}).get("confirmed", []),
        "players_pending": match.get("players", {}).get("pending", []),
        "availability_responses": match.get("negotiation", {}).get(
            "availability_responses", {}
        ),
        "negotiation_rounds": match.get("negotiation", {}).get("rounds", 0),
    }
