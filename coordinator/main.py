"""
CourtSync Coordinator - Single Intelligent Agent
Powered by Gemini 2.0 Flash - Handles ALL coordination logic
"""

import functions_framework
from google.cloud import firestore
from vertexai.generative_models import GenerativeModel
from twilio.rest import Client
import vertexai
import json
import os
from datetime import datetime
from typing import Dict, List, Optional

# Initialize services
db = firestore.Client()
vertexai.init(project=os.getenv('GCP_PROJECT', 'picklebot-488800'), location='us-central1')
gemini = GenerativeModel("gemini-2.0-flash-exp")
twilio_client = Client(
    os.getenv('TWILIO_ACCOUNT_SID'),
    os.getenv('TWILIO_AUTH_TOKEN')
)

WHATSAPP_FROM = os.getenv('TWILIO_WHATSAPP_NUMBER')

class CourtSyncCoordinator:
    """
    Single powerful AI agent that does everything.
    """
    
    def __init__(self):
        self.db = db
        self.ai = gemini
        self.messaging = twilio_client
    
    def process_event(self, event_data: Dict) -> Dict:
        """Main entry point - route to appropriate handler"""
        
        print(f"Processing event: {json.dumps(event_data, indent=2)}")
        
        # WhatsApp message from player
        if 'from' in event_data and 'body' in event_data:
            return self.handle_player_message(
                phone=event_data['from'],
                message=event_data['body']
            )
        
        # Venue cancellation
        elif 'cancellation' in event_data:
            return self.handle_venue_cancellation(event_data)
        
        else:
            print(f"Unknown event type: {event_data}")
            return {'status': 'ignored'}
    
    def handle_player_message(self, phone: str, message: str) -> Dict:
        """
        Player sent WhatsApp message - use Gemini to understand and respond
        """
        
        # Get or create player
        player = self.get_or_create_player(phone)
        
        # Use Gemini to understand intent
        intent = self.understand_message(message, player)
        
        print(f"Intent: {json.dumps(intent, indent=2)}")
        
        # Route based on intent
        action = intent.get('action', 'unknown')
        
        if action == 'create_match':
            return self.create_match_request(phone, intent['details'])
        
        elif action == 'confirm_match':
            return self.confirm_player(phone)
        
        elif action == 'decline_match':
            return self.decline_player(phone)
        
        elif action == 'update_profile':
            return self.update_player_profile(phone, intent['details'])
        
        elif action == 'ask_question':
            return self.answer_question(phone, message, intent)
        
        else:
            self.send_message(phone, "Try: 'Need doubles 3.5 level tomorrow 6pm'")
            return {'status': 'clarification_sent'}
    
    def understand_message(self, message: str, player: Dict) -> Dict:
        """
        THE KEY INTELLIGENCE: Use Gemini to understand player intent
        """
        
        prompt = f"""You are CourtSync, an intelligent pickleball coordination agent.

Player message: "{message}"

Player context: {json.dumps(player, indent=2)}

Understand what they want. Return ONLY valid JSON (no markdown):

{{
  "action": "create_match|confirm_match|decline_match|update_profile|ask_question",
  "details": {{
    // For create_match:
    "format": "doubles|singles|mixed_doubles",
    "skill_level": 3.5,
    "when": "tomorrow 6pm|this weekend|flexible",
    "where": "Riverside Park|near me|flexible",
    "needs_players": 3
    
    // For update_profile:
    "skill_level": 3.5,
    "name": "Mike"
    
    // For ask_question:
    "suggested_response": "Your answer here"
  }},
  "confidence": 0.95
}}

Examples:

"Need doubles 3.5 level tomorrow 6pm"
{{"action": "create_match", "details": {{"format": "doubles", "skill_level": 3.5, "when": "tomorrow 6pm", "where": "near me", "needs_players": 3}}, "confidence": 0.95}}

"YES"
{{"action": "confirm_match", "details": {{}}, "confidence": 1.0}}

"Can't make it"
{{"action": "decline_match", "details": {{}}, "confidence": 0.9}}

"I'm a 4.0 player"
{{"action": "update_profile", "details": {{"skill_level": 4.0}}, "confidence": 0.95}}

Process the message above and return JSON only.
"""
        
        try:
            response = self.ai.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.2,
                    "max_output_tokens": 500
                }
            )
            
            # Parse response
            text = response.text.strip()
            
            # Remove markdown if present
            if '```' in text:
                text = text.split('```json')[1].split('```')[0] if '```json' in text else text
                text = text.split('```')[1].split('```')[0] if text.startswith('```') else text
            
            intent = json.loads(text.strip())
            
            # Low confidence - ask for clarification
            if intent.get('confidence', 0) < 0.7:
                self.send_message(
                    phone,
                    "I'm not sure I understood. Try: 'Need doubles 3.5 level tomorrow 6pm'"
                )
                return {'action': 'ask_question'}
            
            return intent
            
        except Exception as e:
            print(f"Gemini error: {e}")
            self.send_message(
                phone,
                "Sorry, I didn't understand. Try: 'Need doubles 3.5 level tomorrow 6pm'"
            )
            return {'action': 'ask_question'}
    
    def create_match_request(self, initiator: str, details: Dict) -> Dict:
        """
        Player wants a match - find compatible players
        """
        
        # Create match document
        match_ref = self.db.collection('matches').document()
        match_data = {
            'match_id': match_ref.id,
            'initiator': initiator,
            'status': 'seeking',
            'details': details,
            'players': {
                'needed': details.get('needs_players', 3),
                'confirmed': [initiator],
                'pending': []
            },
            'created_at': firestore.SERVER_TIMESTAMP
        }
        match_ref.set(match_data)
        
        # Find compatible players
        candidates = self.find_compatible_players(details)
        
        if not candidates:
            self.send_message(
                initiator,
                f"Looking for {details['format']} players at {details['skill_level']} level. I'll notify you when I find matches!"
            )
            return {'status': 'searching'}
        
        # Send invites
        invited = 0
        for candidate in candidates[:details.get('needs_players', 3)]:
            
            # Generate personalized invite with Gemini
            invite = self.generate_invite_message(candidate, details)
            
            self.send_message(candidate['phone'], invite)
            
            # Track in match
            match_ref.update({
                'players.pending': firestore.ArrayUnion([candidate['phone']])
            })
            
            # Set active match
            self.db.collection('players').document(candidate['phone']).update({
                'state.active_match_id': match_ref.id
            })
            
            invited += 1
        
        # Confirm to initiator
        self.send_message(
            initiator,
            f"Found {invited} players! Asking them now. You'll hear back soon."
        )
        
        # Log activity
        self.log_activity(
            'MATCH_CREATED',
            f"Match created, {invited} players invited",
            {'match_id': match_ref.id}
        )
        
        return {'status': 'invites_sent', 'count': invited}
    
    def find_compatible_players(self, match_details: Dict) -> List[Dict]:
        """
        Find players matching the criteria
        """
        
        skill = match_details.get('skill_level', 3.5)
        
        # Query players in skill range
        players_query = self.db.collection('players')\
            .where('profile.skill_level', '>=', skill - 0.5)\
            .where('profile.skill_level', '<=', skill + 0.5)\
            .limit(20)\
            .stream()
        
        candidates = []
        for doc in players_query:
            player = doc.to_dict()
            
            # Skip if already in a match
            if player.get('state', {}).get('active_match_id'):
                continue
            
            candidates.append({
                'phone': doc.id,
                'name': player['profile'].get('name', 'Player'),
                'skill': player['profile'].get('skill_level'),
                'reliability': player['stats'].get('reliability_score', 1.0)
            })
        
        # Sort by reliability
        candidates.sort(key=lambda x: x['reliability'], reverse=True)
        
        return candidates
    
    def generate_invite_message(self, player: Dict, match_details: Dict) -> str:
        """
        Use Gemini to generate personalized invite
        """
        
        prompt = f"""Generate a friendly WhatsApp invitation for pickleball.

Player: {player['name']} (skill {player['skill']})
Match: {match_details['format']} at {match_details['skill_level']} level {match_details.get('when', 'soon')}

Requirements:
- Under 160 characters
- Friendly tone
- Include 🎾 emoji
- End with "Reply YES to join or NO to pass"

Return ONLY the message text (no quotes, no markdown).
"""
        
        try:
            response = self.ai.generate_content(
                prompt,
                generation_config={"temperature": 0.7, "max_output_tokens": 100}
            )
            return response.text.strip()
        except:
            # Fallback
            return f"🎾 Match available! {match_details['format']} at {match_details['skill_level']} level {match_details.get('when', 'soon')}. Reply YES to join or NO to pass."
    
    def confirm_player(self, phone: str) -> Dict:
        """Player confirmed - add to match"""
        
        player = self.db.collection('players').document(phone).get().to_dict()
        match_id = player.get('state', {}).get('active_match_id')
        
        if not match_id:
            self.send_message(phone, "No active match invitation found.")
            return {'status': 'no_match'}
        
        match_ref = self.db.collection('matches').document(match_id)
        match = match_ref.get().to_dict()
        
        # Add to confirmed
        match_ref.update({
            'players.pending': firestore.ArrayRemove([phone]),
            'players.confirmed': firestore.ArrayUnion([phone])
        })
        
        # Check if full
        updated_match = match_ref.get().to_dict()
        confirmed = len(updated_match['players']['confirmed'])
        needed = updated_match['players']['needed']
        
        if confirmed >= needed:
            # Match complete!
            self.finalize_match(match_id)
        else:
            # Update initiator
            initiator = updated_match['initiator']
            self.send_message(
                initiator,
                f"✅ {confirmed}/{needed} players confirmed! Waiting on {needed - confirmed} more."
            )
            
            self.send_message(phone, f"You're in! Waiting for {needed - confirmed} more players...")
        
        return {'status': 'confirmed'}
    
    def finalize_match(self, match_id: str) -> Dict:
        """
        Match is full - send confirmations
        """
        
        match_ref = self.db.collection('matches').document(match_id)
        match = match_ref.get().to_dict()
        
        # Update status
        match_ref.update({
            'status': 'confirmed',
            'confirmed_at': firestore.SERVER_TIMESTAMP
        })
        
        # Generate confirmation with Gemini
        confirmation = self.generate_confirmation_message(match)
        
        # Send to all players
        for phone in match['players']['confirmed']:
            self.send_message(phone, confirmation)
            
            # Clear active match
            self.db.collection('players').document(phone).update({
                'state.active_match_id': None
            })
        
        # Record revenue if applicable
        if match.get('spot_id'):
            self.record_revenue(match)
        
        # Log activity
        self.log_activity(
            'MATCH_CONFIRMED',
            f"Match confirmed with {len(match['players']['confirmed'])} players",
            {'match_id': match_id}
        )
        
        return {'status': 'finalized'}
    
    def generate_confirmation_message(self, match: Dict) -> str:
        """Generate nice confirmation with Gemini"""
        
        prompt = f"""Generate a confirmation message for a pickleball match.

Match: {json.dumps(match['details'], indent=2)}
Players: {len(match['players']['confirmed'])}

Requirements:
- Friendly and exciting
- Include details (when, where, format)
- Use 🎾 and ✅ emojis
- Under 200 characters
- End with "See you there!"

Return ONLY the message text.
"""
        
        try:
            response = self.ai.generate_content(prompt)
            return response.text.strip()
        except:
            details = match['details']
            return f"✅ Match confirmed! 🎾\n\n{details['format']} at {details.get('skill_level', 'your')} level\n{details.get('when', 'Soon')}\n{details.get('where', 'Local courts')}\n\nSee you there!"
    
    def decline_player(self, phone: str) -> Dict:
        """Player declined"""
        
        player = self.db.collection('players').document(phone).get().to_dict()
        match_id = player.get('state', {}).get('active_match_id')
        
        if match_id:
            match_ref = self.db.collection('matches').document(match_id)
            match_ref.update({
                'players.pending': firestore.ArrayRemove([phone]),
                'players.declined': firestore.ArrayUnion([phone])
            })
            
            self.db.collection('players').document(phone).update({
                'state.active_match_id': None
            })
        
        self.send_message(phone, "No problem! I'll keep you in mind for future matches.")
        
        return {'status': 'declined'}
    
    def handle_venue_cancellation(self, event_data: Dict) -> Dict:
        """
        Venue has cancellation - auto-fill it
        """
        
        cancellation = event_data['cancellation']
        
        # Create spot
        spot_ref = self.db.collection('spots').document()
        spot_ref.set({
            'spot_id': spot_ref.id,
            'venue': event_data.get('venue', {}),
            'details': cancellation,
            'status': 'available',
            'created_at': firestore.SERVER_TIMESTAMP
        })
        
        # Create match to fill it
        match_details = {
            'format': cancellation.get('activity', 'doubles').replace('pickleball_', ''),
            'skill_level': cancellation.get('skill_level', 3.5),
            'when': cancellation.get('time_slot'),
            'where': event_data.get('venue', {}).get('name', 'venue'),
            'needs_players': 4
        }
        
        match_ref = self.db.collection('matches').document()
        match_ref.set({
            'match_id': match_ref.id,
            'initiator': 'system',
            'spot_id': spot_ref.id,
            'status': 'seeking',
            'details': match_details,
            'players': {'needed': 4, 'confirmed': [], 'pending': []},
            'revenue': {'value': cancellation.get('value', 40)},
            'created_at': firestore.SERVER_TIMESTAMP
        })
        
        # Find and invite players
        candidates = self.find_compatible_players(match_details)
        for candidate in candidates[:4]:
            invite = self.generate_invite_message(candidate, match_details)
            self.send_message(candidate['phone'], invite)
            
            match_ref.update({
                'players.pending': firestore.ArrayUnion([candidate['phone']])
            })
            
            self.db.collection('players').document(candidate['phone']).update({
                'state.active_match_id': match_ref.id
            })
        
        self.log_activity(
            'SPOT_DETECTED',
            f"Cancellation detected, {len(candidates[:4])} players invited",
            {'spot_id': spot_ref.id}
        )
        
        return {'status': 'processing', 'invited': len(candidates[:4])}
    
    def record_revenue(self, match: Dict):
        """Record revenue event"""
        
        self.db.collection('revenue_events').add({
            'match_id': match['match_id'],
            'spot_id': match.get('spot_id'),
            'revenue': match.get('revenue', {}),
            'timestamp': firestore.SERVER_TIMESTAMP
        })
    
    def send_message(self, to_phone: str, message: str):
        """Send WhatsApp via Twilio"""
        
        try:
            self.messaging.messages.create(
                from_=f"whatsapp:{WHATSAPP_FROM}",
                to=f"whatsapp:{to_phone}",
                body=message
            )
            print(f"Sent to {to_phone}: {message}")
        except Exception as e:
            print(f"Error sending to {to_phone}: {e}")
    
    def log_activity(self, activity_type: str, description: str, metadata: Dict = None):
        """Log for dashboard"""
        
        self.db.collection('activity_log').add({
            'type': activity_type,
            'description': description,
            'metadata': metadata or {},
            'timestamp': firestore.SERVER_TIMESTAMP
        })
    
    def get_or_create_player(self, phone: str) -> Dict:
        """Get or create player profile"""
        
        player_ref = self.db.collection('players').document(phone)
        player_doc = player_ref.get()
        
        if player_doc.exists:
            player = player_doc.to_dict()
            player['phone'] = phone
            return player
        
        # New player
        new_player = {
            'phone': phone,
            'profile': {'created_at': firestore.SERVER_TIMESTAMP},
            'preferences': {'formats': ['doubles']},
            'stats': {'matches_played': 0, 'reliability_score': 1.0},
            'subscription': {'tier': 'free', 'matches_this_month': 0, 'matches_limit': 4},
            'state': {'onboarding_complete': False}
        }
        
        player_ref.set(new_player)
        
        self.send_message(
            phone,
            "Welcome to CourtSync! 🎾\n\nWhat's your skill level? (Reply with a number like 3.5)"
        )
        
        return new_player
    
    def update_player_profile(self, phone: str, details: Dict) -> Dict:
        """Update player profile"""
        
        updates = {}
        
        if 'skill_level' in details:
            updates['profile.skill_level'] = details['skill_level']
            updates['state.onboarding_complete'] = True
        
        if 'name' in details:
            updates['profile.name'] = details['name']
        
        if updates:
            self.db.collection('players').document(phone).update(updates)
            self.send_message(phone, "✅ Profile updated! Ready to find you matches.")
        
        return {'status': 'updated'}
    
    def answer_question(self, phone: str, question: str, intent: Dict) -> Dict:
        """Answer player questions"""
        
        suggested = intent.get('details', {}).get('suggested_response')
        
        if suggested:
            self.send_message(phone, suggested)
        else:
            self.send_message(
                phone,
                "I help coordinate pickleball matches! Try: 'Need doubles 3.5 level tomorrow 6pm'"
            )
        
        return {'status': 'answered'}

# Initialize coordinator
coordinator = CourtSyncCoordinator()

# Cloud Function entry point
@functions_framework.cloud_event
def process_event(cloud_event):
    """Entry point for Cloud Function"""
    
    # Decode Pub/Sub message
    import base64
    message_data = base64.b64decode(cloud_event.data["message"]["data"]).decode()
    event_data = json.loads(message_data)
    
    # Process through coordinator
    return coordinator.process_event(event_data)