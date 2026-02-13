import json
import logging
import pandas as pd
from typing import List, Dict, Optional
from functools import lru_cache
import os

logger = logging.getLogger("tnea_ai.data")

class DataEngine:
    _instance = None
    
    def __new__(cls, data_dir: str = None):
        if cls._instance is None:
            cls._instance = super(DataEngine, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, data_dir: str = None):
        if self._initialized:
            return
        
        if data_dir is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            self.data_dir = os.path.join(base_dir, "data")
        else:
            self.data_dir = data_dir
            
        self.colleges = []
        self.college_locations = []
        self.branches = []
        self.branch_trends = {}
        self.cutoffs = []
        self.seats = []
        self.guidelines = ""
        self.percentile_ranges = None
        
        # Indexes for fast lookup
        self._cutoff_index: Dict[str, List[Dict]] = {}
        self._seat_index: Dict[str, List[Dict]] = {}
            
        self.load_data()
        self._build_indexes()
        self._initialized = True

    def load_data(self):
        """Loads all necessary data files."""
        try:
            with open(os.path.join(self.data_dir, "json/colleges.json"), "r") as f:
                self.colleges = json.load(f)
            
            with open(os.path.join(self.data_dir, "json/college_geo_locations.json"), "r") as f:
                self.college_locations = json.load(f)
                
            with open(os.path.join(self.data_dir, "json/branches.json"), "r") as f:
                self.branches = json.load(f)
                
            with open(os.path.join(self.data_dir, "json/branch_trends.json"), "r") as f:
                self.branch_trends = json.load(f)

            with open(os.path.join(self.data_dir, "json/cutoffs.json"), "r") as f:
                self.cutoffs = json.load(f)

            with open(os.path.join(self.data_dir, "json/seats.json"), "r") as f:
                self.seats = json.load(f)
                
            logger.info(f"Loaded {len(self.colleges)} colleges, {len(self.cutoffs)} cutoffs, {len(self.seats)} seats")
        except Exception as e:
            logger.error(f"Error loading JSON data: {e}")

        try:
           self.percentile_ranges = pd.read_csv(os.path.join(self.data_dir, "csv/percentile_ranges.csv"))
           logger.info(f"Loaded {len(self.percentile_ranges)} percentile range records")
        except Exception as e:
            logger.error(f"Error loading CSV data: {e}")

        try:
            with open(os.path.join(self.data_dir, "docs/tnea_guidelines.txt"), "r") as f:
                self.guidelines = f.read()
        except Exception as e:
            logger.error(f"Error loading text data: {e}")

    def _build_indexes(self):
        """Build hash indexes for O(1) lookup by college_code."""
        self._cutoff_index = {}
        for c in self.cutoffs:
            code = str(c.get('college_code'))
            if code not in self._cutoff_index:
                self._cutoff_index[code] = []
            self._cutoff_index[code].append(c)
        
        self._seat_index = {}
        for s in self.seats:
            code = str(s.get('college_code'))
            if code not in self._seat_index:
                self._seat_index[code] = []
            self._seat_index[code].append(s)
        
        logger.info(f"Built indexes: {len(self._cutoff_index)} college cutoff groups, {len(self._seat_index)} college seat groups")

    def get_college_by_code(self, code: str) -> Optional[Dict]:
        """Retrieves college details by code."""
        for college in self.colleges:
            if str(college.get("code")) == str(code):
                return college
        return None

    def search_colleges(self, query: str) -> List[Dict]:
        """Search colleges by name or code."""
        query = query.lower()
        results = []
        for college in self.colleges:
            if query in college.get("name", "").lower() or query in str(college.get("code", "")):
                results.append(college)
        return results

    def get_colleges_by_location(self, location_query: str) -> List[Dict]:
        """Finds colleges matching the location string (District/City)."""
        location_query = location_query.lower()
        results = []
        for college in self.colleges:
            if location_query in str(college).lower():
                 results.append(college)
        return results

    def get_branch_trends(self, branch_code: str) -> Dict:
        """Retrieves trend data for a specific branch."""
        return self.branch_trends.get(branch_code, {})

    def get_college_cutoffs(self, college_code: str) -> List[Dict]:
        """Retrieves cutoff data for a college using index (O(1))."""
        return self._cutoff_index.get(str(college_code), [])

    def get_college_seats(self, college_code: str) -> List[Dict]:
        """Retrieves seat matrix for a college using index (O(1))."""
        return self._seat_index.get(str(college_code), [])

    def get_total_seats_for_college(self, college_code: str, branch_code: str = None) -> int:
        """Get total seat count for a college, optionally filtered by branch."""
        seats = self.get_college_seats(str(college_code))
        total = 0
        for s in seats:
            if branch_code and str(s.get('branch_code', '')) != str(branch_code):
                continue
            # 'total' field is the seat count; 'seats' is a dict of community-wise breakdown
            seat_val = s.get('total', 0)
            if isinstance(seat_val, (int, float)):
                total += int(seat_val)
            elif isinstance(seat_val, str) and seat_val.isdigit():
                total += int(seat_val)
        return total

    def get_guidelines(self) -> str:
        """Returns the TNEA guidelines text."""
        return self.guidelines

if __name__ == "__main__":
    engine = DataEngine()
    logger.info(f"Loaded {len(engine.colleges)} colleges.")
    logger.info(f"Loaded {len(engine.branches)} branches.")
    if engine.percentile_ranges is not None and not engine.percentile_ranges.empty:
        logger.info("Percentile data loaded.")
