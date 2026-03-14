import requests
import logging
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import text
from task_publish.utils.math import haversine

logger = logging.getLogger(__name__)

def find_nearby_parks(db: Session, lat: float, lng: float, user_id: str, radius_m: int = 2000) -> List[Dict[str, Any]]:
    query = (f"[out:json][timeout:8]; node[\"leisure\"=\"park\"]"
             f"(around:{radius_m},{lat},{lng}); out body 3;")
    
    parks = []
    try:
        resp = requests.post("https://overpass-api.de/api/interpreter", data=query, timeout=10)
        resp.raise_for_status()
        elems = resp.json().get("elements", [])
        
        parks = [
            {
                "name": e.get("tags", {}).get("name", "Nearby park"),
                "lat": e["lat"],
                "lng": e["lon"],
                "distance_m": int(haversine(lat, lng, e["lat"], e["lon"]))
            }
            for e in elems[:3]
        ]
    except Exception as e:
        logger.error(f"Overpass API error for user {user_id}: {e}")

    if not parks:
        # user_known_places fallback mock
        pl_row = db.execute(text("SELECT * FROM user_known_places WHERE user_id = :u ORDER BY id LIMIT 1"), {"u": user_id}).fetchone()
        if pl_row:
            parks = [{
                "name": pl_row.place_name,
                "lat": float(pl_row.gps_lat),
                "lng": float(pl_row.gps_lng),
                "distance_m": 0
            }]
        else:
            logger.warning(f"overpass_empty fallback: giving a mock park for {user_id}")
            parks = [{
                "name": "Fallback Park",
                "lat": 1.3521,
                "lng": 103.8198,
                "distance_m": 0
            }]
            
    return parks
