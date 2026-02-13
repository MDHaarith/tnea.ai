from typing import List, Dict

class Eligibility:
    def check_eligibility(self, user_mark: float, college_cutoffs: List[Dict], branch_code: str = None) -> bool:
        """
        Checks if user mark is sufficient for college/branch based on last year's cutoff.
        Simple check: User Mark >= Last Cutoff - 5 (Buffer)
        """
        if not college_cutoffs:
            return False # No data, assume not eligible for safety or handle differently
            
        for cutoff_record in college_cutoffs:
            if branch_code and str(cutoff_record.get('branch_code')) != str(branch_code):
                continue
                
            cutoff_mark = float(cutoff_record.get('cutoff_mark', 200)) # Default high if missing
            if user_mark >= (cutoff_mark - 5): # Buffer of 5 marks
                return True
        return False
