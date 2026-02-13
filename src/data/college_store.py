from typing import List, Dict, Optional
from data.loader import DataEngine
from utils.normalizers import normalize_name

class CollegeStore:
    def __init__(self):
        self.data_engine = DataEngine() # Singleton

    def get_all_colleges(self) -> List[Dict]:
        return self.data_engine.colleges

    def get_college_by_code(self, code: str) -> Optional[Dict]:
        return self.data_engine.get_college_by_code(code)

    def search_colleges(self, query: str) -> List[Dict]:
        return self.data_engine.search_colleges(query)

    def filter_by_location(self, location: str) -> List[Dict]:
        return self.data_engine.get_colleges_by_location(location)

    def get_college_geo_location(self, code: str) -> Optional[Dict]:
        # Assuming geo_locations list has 'code' key
        for loc in self.data_engine.college_locations:
             if str(loc.get("code")) == str(code):
                 return loc
        return None
