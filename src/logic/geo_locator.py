import math
import logging
import difflib
from typing import List, Dict, Optional
from data.college_store import CollegeStore
from data.loader import DataEngine
from utils.normalizers import normalize_query

logger = logging.getLogger("tnea_ai.geo")


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great-circle distance between two points on Earth (in km)."""
    R = 6371  # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


class GeoLocator:
    def __init__(self):
        self.college_store = CollegeStore()
        self.data_engine = DataEngine()
        self._district_centers: Dict[str, tuple] = {}
        self._build_district_centers()

    def _build_district_centers(self):
        """Compute average lat/lng per district from college data."""
        district_coords: Dict[str, List[tuple]] = {}
        for college in self.data_engine.colleges:
            district = (college.get('district') or '').upper().strip()
            lat = college.get('lat')
            lng = college.get('lng')
            if district and lat and lng:
                if district not in district_coords:
                    district_coords[district] = []
                district_coords[district].append((float(lat), float(lng)))
        
        for district, coords in district_coords.items():
            avg_lat = sum(c[0] for c in coords) / len(coords)
            avg_lng = sum(c[1] for c in coords) / len(coords)
            self._district_centers[district] = (avg_lat, avg_lng)
        
        logger.info(f"Built geo centers for {len(self._district_centers)} districts")

    def _resolve_location(self, location: str) -> Optional[tuple]:
        """Resolve a location string to (lat, lng). Tries district match, then college name."""
        loc_upper = location.upper().strip()
        
        # Direct district match
        if loc_upper in self._district_centers:
            return self._district_centers[loc_upper]
        
        # Fuzzy district match (substring)
        for district, center in self._district_centers.items():
            if loc_upper in district or district in loc_upper:
                return center
                
        # Fuzzy match using difflib for typos (e.g. "aryalur" -> "ARIYALUR")
        matches = difflib.get_close_matches(loc_upper, self._district_centers.keys(), n=1, cutoff=0.7)
        if matches:
            logger.info(f"Fuzzy matched location '{location}' to '{matches[0]}'")
            return self._district_centers[matches[0]]
        
        # Try matching a college name and using its coordinates
        for college in self.data_engine.colleges:
            if loc_upper in (college.get('name') or '').upper():
                lat = college.get('lat')
                lng = college.get('lng')
                if lat and lng:
                    return (float(lat), float(lng))
        
        return None

    def find_nearby_colleges(self, location: str, radius_km: int = 100) -> List[Dict]:
        """
        Find colleges near a location using actual haversine distance.
        Falls back to string matching if geo resolution fails.
        """
        center = self._resolve_location(location)
        
        if center is None:
            # Fallback to string matching
            logger.info(f"Geo resolution failed for '{location}', falling back to string match")
            loc = normalize_query(location)
            if not loc:
                return []
            return self.college_store.filter_by_location(loc)
        
        center_lat, center_lng = center
        results = []
        
        for college in self.data_engine.colleges:
            lat = college.get('lat')
            lng = college.get('lng')
            if lat is None or lng is None:
                continue
            
            dist = haversine_km(center_lat, center_lng, float(lat), float(lng))
            if dist <= radius_km:
                college_copy = dict(college)
                college_copy['_distance_km'] = round(dist, 1)
                results.append(college_copy)
        
        # Sort by distance
        results.sort(key=lambda c: c.get('_distance_km', 999))
        logger.info(f"Found {len(results)} colleges within {radius_km}km of '{location}'")
        return results
