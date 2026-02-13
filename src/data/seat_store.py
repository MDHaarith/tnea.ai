from typing import List, Dict
from data.loader import DataEngine

class SeatStore:
    def __init__(self):
        self.data_engine = DataEngine()

    def get_seats_by_college(self, college_code: str) -> List[Dict]:
        return self.data_engine.get_college_seats(college_code)

    def has_management_quota(self, college_code: str) -> bool:
        seats = self.get_seats_by_college(college_code)
        for s in seats:
             cat = s.get('category', '').lower()
             if 'mq' in cat or 'management' in cat:
                 return True
        return False
