from typing import List, Dict, Tuple

class ChoiceStrategy:
    def calculate_composite_score(self, option: Dict, user_mark: float, user_location: str = None) -> float:
        """
        Calculates a 0-100 quality score for a college option.
        Factors: Placement (40%), Autonomous (15%), Location (10%), Cutoff Proxy (30%), Seats (5%)
        """
        score = 0.0
        
        # 1. Placement (Max 40)
        placement_str = str(option.get('placement', '0')).replace('%', '')
        try:
            placement_val = float(placement_str)
            score += min(40, placement_val * 0.4)
        except ValueError:
            pass
            
        # 2. Cutoff Proxy (Max 30) - Higher cutoff implies better college quality generally
        # Normalize: 200 cutoff -> 30 points, 100 cutoff -> 15 points
        cutoff = float(option.get('cutoff_mark', 0))
        score += min(30, (cutoff / 200.0) * 30)
        
        # 3. Autonomous (Max 15)
        if "Autonomous" in str(option.get('autonomous', '')):
            score += 15
            
        # 4. Location Match (Max 10)
        if user_location and user_location.lower() in str(option.get('district', '')).lower():
            score += 10
            
        # 5. Seat Availability (Max 5) - More seats = generally bigger dept
        seats = option.get('total_seats')
        if seats and isinstance(seats, (int, float)) and seats > 60:
            score += 5
            
        return round(score, 1)

    def categorize_options(self, user_mark: float, options: List[Dict], user_location: str = None) -> Dict[str, List[Dict]]:
        """
        Categorizes colleges into Safe, Moderate, Ambitious based on cutoff.
        Sorts each category by Composite Quality Score.
        """
        categorized = {
            "Safe": [],
            "Moderate": [],
            "Ambitious": []
        }
        
        for option in options:
            cutoff = float(option.get('cutoff_mark', 0))
            
            # Calculate and attach score
            option['quality_score'] = self.calculate_composite_score(option, user_mark, user_location)
            
            if user_mark >= (cutoff + 2):
                categorized["Safe"].append(option)
            elif (cutoff - 5) <= user_mark < (cutoff + 2):
                categorized["Moderate"].append(option)
            elif (cutoff - 10) <= user_mark < (cutoff - 5):
                categorized["Ambitious"].append(option)
        
        # Sort by Quality Score descending
        for cat in categorized:
            categorized[cat].sort(key=lambda x: x['quality_score'], reverse=True)
                
        return categorized
