"""
CourtSync - Skill Matcher
Finds compatible players based on skill level, location, format, and reliability.
"""

import logging
from typing import Dict, List, Optional

from google.cloud import firestore
from geopy.distance import geodesic

logger = logging.getLogger(__name__)

# Maximum distance (km) to consider players "nearby"
MAX_DISTANCE_KM = 25


class SkillMatcher:
    """Intelligent player matching: skill × location × format × reliability."""

    def __init__(self, db: firestore.Client):
        self.db = db

    def find_compatible_players(
        self,
        skill_target: float,
        skill_range: List[float],
        format_pref: str,
        location: Optional[Dict],
        exclude_player: str,
        limit: int = 10,
    ) -> List[Dict]:
        """
        Return ranked list of compatible players.

        Args:
            skill_target:   Ideal skill level (e.g. 3.5)
            skill_range:    [min, max] acceptable range
            format_pref:    'singles' | 'doubles' | 'mixed_doubles'
            location:       {'lat': float, 'lng': float} of requesting player
            exclude_player: Phone number to exclude from results
            limit:          Max candidates to return

        Returns:
            List of player dicts ordered by compatibility score (desc)
        """
        skill_min, skill_max = skill_range[0], skill_range[1]

        # Pull all onboarded players with a DUPR rating
        query = (
            self.db.collection("players")
            .where("onboarding_complete", "==", True)
            .where("profile.dupr_rating", ">=", skill_min)
            .where("profile.dupr_rating", "<=", skill_max)
        )

        candidates = []
        for doc in query.stream():
            player = doc.to_dict()
            phone = player.get("phone")

            if phone == exclude_player:
                continue

            # Format filter
            prefs = player.get("preferences", {}).get("formats", [])
            if format_pref not in prefs and "doubles" not in prefs:
                continue

            # Skip players already in an active match
            if player.get("active_match_id"):
                continue

            score = self._score_candidate(
                player=player,
                skill_target=skill_target,
                location=location,
            )
            candidates.append(
                {
                    "phone": phone,
                    "name": player["profile"].get("name"),
                    "dupr_rating": player["profile"].get("dupr_rating"),
                    "reliability_score": player.get("stats", {}).get(
                        "reliability_score", 1.0
                    ),
                    "score": score,
                }
            )

        candidates.sort(key=lambda x: x["score"], reverse=True)
        return candidates[:limit]

    def _score_candidate(
        self,
        player: Dict,
        skill_target: float,
        location: Optional[Dict],
    ) -> float:
        """
        Composite score (0–100) weighting:
          - Skill proximity  (40 pts)
          - Geographic proximity (30 pts)
          - Reliability score (20 pts)
          - Play frequency / engagement (10 pts)
        """
        score = 0.0

        # Skill proximity (closer = better)
        dupr = player["profile"].get("dupr_rating", skill_target)
        skill_diff = abs(dupr - skill_target)
        score += max(0, 40 - (skill_diff * 40))

        # Geographic proximity
        player_loc = player.get("profile", {}).get("location")
        if location and player_loc:
            try:
                dist_km = geodesic(
                    (location["lat"], location["lng"]),
                    (player_loc["lat"], player_loc["lng"]),
                ).km
                geo_score = max(0, 30 - (dist_km / MAX_DISTANCE_KM) * 30)
                score += geo_score
            except Exception:
                score += 15  # Neutral if geo calc fails
        else:
            score += 15

        # Reliability (no-show history)
        reliability = player.get("stats", {}).get("reliability_score", 1.0)
        score += reliability * 20

        # Engagement (played recently)
        matches_played = player.get("stats", {}).get("matches_played", 0)
        score += min(10, matches_played * 0.5)

        return round(score, 2)
