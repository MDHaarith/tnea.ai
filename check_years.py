
import json
import os
import sys

def check_cutoff_years():
    base_dir = "/home/mdhaarith/Desktop/PROJECT/TNEA_AI/Launched/tnea.ai/data/json"
    try:
        with open(os.path.join(base_dir, "cutoffs.json"), "r") as f:
            cutoffs = json.load(f)
            
        print(f"Total cutoff records: {len(cutoffs)}")
        
        years = set()
        college_counts = {}
        
        for c in cutoffs:
            years.add(c.get('year'))
            code = str(c.get('college_code'))
            if code not in college_counts:
                college_counts[code] = set()
            college_counts[code].add(c.get('year'))
            
        print(f"Available years in data: {sorted(list(years))}")
        
        # Sample a few colleges
        print("\nSample college data:")
        sample_codes = list(college_counts.keys())[:5]
        for code in sample_codes:
            print(f"College {code} has years: {sorted(list(college_counts[code]))}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_cutoff_years()
