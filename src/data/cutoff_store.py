from typing import List, Dict
from data.loader import DataEngine

class CutoffStore:
    def __init__(self):
        self.data_engine = DataEngine()

    def get_cutoffs_by_college(self, college_code: str) -> List[Dict]:
        return self.data_engine.get_college_cutoffs(college_code)

    def get_cutoffs_by_branch(self, branch_code: str) -> List[Dict]:
        # This might be slow if implemented naively in loader, assuming we just filter the full list
        # For now, we rely on loader's comprehensive list if available, or just implement filtering here
        # But data_engine.cutoffs is the master list
        return self.data_engine.get_cutoffs_by_branch(branch_code)
