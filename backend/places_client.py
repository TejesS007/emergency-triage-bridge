import logging
import math
import os
from typing import Optional
import httpx

from backend.schema import NearestHospital

logger = logging.getLogger(__name__)

# Hardcoded reference coordinates: Bangalore City Center
BANGALORE_LAT = 12.9716
BANGALORE_LNG = 77.5946

FALLBACK_HOSPITAL = NearestHospital(
    name="Bangalore Medical Center & Victoria Hospital",
    distance_km=1.25,
    address="Victoria Hospital Campus, Fort Rd, Kalasipalya, Bengaluru, Karnataka 560002",
)

PLACES_SEARCH_URL = "https://places.googleapis.com/v1/places:searchNearby"


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the Great Circle / Haversine distance in kilometers between two GPS points."""
    r = 6371.0  # Earth's radius in kilometers
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = (
        math.sin(d_lat / 2.0) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(d_lon / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return round(r * c, 2)


def get_nearest_hospital(
    lat: float = BANGALORE_LAT,
    lng: float = BANGALORE_LNG,
) -> NearestHospital:
    """
    Calls the Google Places API (New) to locate the nearest hospital to the given coordinates.
    Computes distance in km and returns a NearestHospital object.
    Falls back gracefully if the API key is absent or an error occurs.
    """
    api_key = os.environ.get("GOOGLE_PLACES_API_KEY")
    if not api_key:
        logger.warning("GOOGLE_PLACES_API_KEY is not configured; using fallback hospital.")
        return FALLBACK_HOSPITAL

    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": "places.displayName,places.location,places.formattedAddress",
    }

    payload = {
        "includedTypes": ["hospital"],
        "maxResultCount": 1,
        "locationRestriction": {
          "circle": {
            "center": {
              "latitude": lat,
              "longitude": lng,
            },
            "radius": 10000.0,
          }
        },
    }

    try:
        with httpx.Client(timeout=5.0) as client:
            response = client.post(PLACES_SEARCH_URL, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()

            places = data.get("places", [])
            if not places:
                logger.info("No nearby hospitals found in Places API response; using fallback.")
                return FALLBACK_HOSPITAL

            first_place = places[0]
            display_name = (
                first_place.get("displayName", {}).get("text")
                or "Local Emergency Hospital"
            )
            location = first_place.get("location", {})
            hosp_lat = location.get("latitude")
            hosp_lng = location.get("longitude")
            address = first_place.get("formattedAddress")

            if hosp_lat is not None and hosp_lng is not None:
                dist = haversine_distance(lat, lng, float(hosp_lat), float(hosp_lng))
            else:
                dist = 1.5

            return NearestHospital(
                name=display_name,
                distance_km=dist,
                address=address,
            )

    except Exception as exc:
        logger.error(f"Google Places API request failed: {exc}", exc_info=True)
        return FALLBACK_HOSPITAL
