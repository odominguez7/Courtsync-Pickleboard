"""
Seed sample data for testing
"""

from google.cloud import firestore
import os

os.environ['GCP_PROJECT'] = 'picklebot-488800'
db = firestore.Client()

# Sample players
players = [
    {
        'phone': '+16175551001',
        'profile': {
            'name': 'Mike Chen',
            'skill_level': 3.5,
            'location': {'lat': 42.3601, 'lng': -71.0589, 'city': 'Boston'}
        },
        'preferences': {'formats': ['doubles'], 'max_drive_minutes': 15},
        'stats': {'matches_played': 12, 'reliability_score': 0.95},
        'subscription': {'tier': 'free', 'matches_this_month': 2, 'matches_limit': 4},
        'state': {'onboarding_complete': True}
    },
    {
        'phone': '+16175551002',
        'profile': {
            'name': 'Sarah Johnson',
            'skill_level': 3.6,
            'location': {'lat': 42.3736, 'lng': -71.1097, 'city': 'Cambridge'}
        },
        'preferences': {'formats': ['doubles', 'mixed_doubles'], 'max_drive_minutes': 20},
        'stats': {'matches_played': 8, 'reliability_score': 1.0},
        'subscription': {'tier': 'premium', 'matches_this_month': 6, 'matches_limit': 999},
        'state': {'onboarding_complete': True}
    },
    {
        'phone': '+16175551003',
        'profile': {
            'name': 'Tom Rodriguez',
            'skill_level': 3.4,
            'location': {'lat': 42.3478, 'lng': -71.0466, 'city': 'Boston'}
        },
        'preferences': {'formats': ['doubles'], 'max_drive_minutes': 10},
        'stats': {'matches_played': 15, 'reliability_score': 0.87},
        'subscription': {'tier': 'free', 'matches_this_month': 3, 'matches_limit': 4},
        'state': {'onboarding_complete': True}
    }
]

print("Seeding players...")
for player in players:
    phone = player['phone']
    db.collection('players').document(phone).set(player)
    print(f"  ✅ Created player: {player['profile']['name']}")

print("\n✅ Seed data loaded!")
print("\nTest by texting: 'Need doubles 3.5 level tomorrow 6pm'")