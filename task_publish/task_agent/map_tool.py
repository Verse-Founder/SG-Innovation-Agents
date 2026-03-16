import requests
import logging
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import text
from task_publish.utils.math import haversine
from task_publish.config import settings

logger = logging.getLogger(__name__)

def find_nearby_parks(db: Session, lat: float, lng: float, user_id: str, radius_m: int = 2000) -> List[Dict[str, Any]]:
    parks = []
    
    # Check if Google Maps API key is configured
    api_key = settings.google_maps_api_key
    if not api_key or api_key == "dummy_key":
        logger.warning(f"Google Maps API key not set! Fallback for user {user_id}")
    else:
        try:
            url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
            params = {
                "location": f"{lat},{lng}",
                "radius": radius_m,
                "type": "park",
                "key": api_key
            }
            resp = requests.get(url, params=params, timeout=10)
            resp.raise_for_status()
            
            data = resp.json()
            if data.get("status") == "OK":
                results = data.get("results", [])
                
                for r in results[:3]:
                    p_lat = r["geometry"]["location"]["lat"]
                    p_lng = r["geometry"]["location"]["lng"]
                    
                    parks.append({
                        "name": r.get("name", "Nearby park"),
                        "lat": p_lat,
                        "lng": p_lng,
                        "distance_m": int(haversine(lat, lng, p_lat, p_lng))
                    })
            else:
                logger.error(f"Google Places API Error: {data.get('status')} - {data.get('error_message', '')}")
                
        except Exception as e:
            logger.error(f"Google Places API Request error for user {user_id}: {e}")

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
            logger.warning(f"Google_empty fallback: giving a mock park for {user_id}")
            parks = [{
                "name": "Fallback Park",
                "lat": 1.3521,
                "lng": 103.8198,
                "distance_m": 0
            }]
            
    return parks
