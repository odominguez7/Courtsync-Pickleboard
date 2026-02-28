"""
CourtSync API Gateway
Receives webhooks and publishes to Pub/Sub for processing
"""

from fastapi import FastAPI, Request, Header, HTTPException
from fastapi.responses import Response
from google.cloud import pubsub_v1, firestore
import hmac
import hashlib
import os
import json

app = FastAPI(title="CourtSync API Gateway")

publisher = pubsub_v1.PublisherClient()
project_id = os.getenv('GCP_PROJECT', 'picklebot-488800')
topic_path = publisher.topic_path(project_id, 'events')

def verify_twilio_signature(url: str, params: dict, signature: str) -> bool:
    """Verify request is from Twilio"""
    token = os.getenv('TWILIO_AUTH_TOKEN', '')
    data = url + ''.join(f'{k}{params[k]}' for k in sorted(params.keys()))
    expected = hmac.new(token.encode(), data.encode(), hashlib.sha1)
    return hmac.compare_digest(expected.digest(), bytes.fromhex(signature))

@app.post("/webhooks/whatsapp")
async def whatsapp_webhook(
    request: Request,
    x_twilio_signature: str = Header(None)
):
    """
    Receive WhatsApp messages from Twilio
    """
    
    form_data = await request.form()
    
    # Verify signature (uncomment for production)
    # if not verify_twilio_signature(str(request.url), dict(form_data), x_twilio_signature):
    #     raise HTTPException(403, "Invalid signature")
    
    # Extract message data
    message_data = {
        'from': form_data.get('From', '').replace('whatsapp:', ''),
        'body': form_data.get('Body', ''),
        'timestamp': firestore.SERVER_TIMESTAMP
    }
    
    # Publish to Pub/Sub
    publisher.publish(
        topic_path,
        json.dumps(message_data).encode('utf-8')
    )
    
    # Return empty TwiML
    return Response(
        content='<?xml version="1.0" encoding="UTF-8"?><Response></Response>',
        media_type='application/xml'
    )

@app.post("/webhooks/venue")
async def venue_webhook(
    request: Request,
    authorization: str = Header(None)
):
    """
    Receive venue cancellations
    """
    
    if not authorization or not authorization.startswith('Bearer '):
        raise HTTPException(401, "Missing authorization")
    
    data = await request.json()
    
    # Publish to Pub/Sub
    publisher.publish(
        topic_path,
        json.dumps(data).encode('utf-8')
    )
    
    return {"success": True, "status": "processing"}

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "api-gateway",
        "version": "1.0.0"
    }

@app.get("/")
async def root():
    return {"message": "CourtSync API Gateway", "status": "running"}