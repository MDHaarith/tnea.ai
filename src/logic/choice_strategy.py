from typing import List, Dict, Tuple

class ChoiceStrategy:
    def categorize_options(self, user_mark: float, options: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Categorizes colleges into Safe, Moderate, Ambitious based on cutoff.
        Safe: Mark >= Cutoff + 2
        Moderate: Cutoff - 5 <= Mark < Cutoff + 2
        Ambitious: Mark < Cutoff - 5 (but within 10)
        """
        categorized = {
            "Safe": [],
            "Moderate": [],
            "Ambitious": []
        }
        
        for option in options:
            cutoff = float(option.get('cutoff_mark', 0))
            if user_mark >= (cutoff + 2):
                categorized["Safe"].append(option)
            elif (cutoff - 5) <= user_mark < (cutoff + 2):
                categorized["Moderate"].append(option)
            elif (cutoff - 10) <= user_mark < (cutoff - 5):
                categorized["Ambitious"].append(option)
                
        return categorized
