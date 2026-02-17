import json
import logging
import pandas as pd
from typing import List, Dict, Optional
from functools import lru_cache
import os
import sqlite3

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
        # self.cutoffs = [] # Removed in favor of SQLite
        # self.seats = []   # Removed in favor of SQLite
        self.guidelines = ""
        self.percentile_ranges = None
        
        # SQLite Connection
        self.db_path = os.path.join(self.data_dir, "tnea.db")
        self.conn = None
        try:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
        except Exception as e:
            logger.error(f"Failed to connect to SQLite DB at {self.db_path}: {e}")
            
        self.load_data()
        self._initialized = True

    def load_data(self):
        """Loads all necessary data files (small JSONs only)."""
        try:
            with open(os.path.join(self.data_dir, "json/colleges.json"), "r") as f:
                self.colleges = json.load(f)
            
            with open(os.path.join(self.data_dir, "json/college_geo_locations.json"), "r") as f:
                self.college_locations = json.load(f)
                
            with open(os.path.join(self.data_dir, "json/branches.json"), "r") as f:
                self.branches = json.load(f)
                
            with open(os.path.join(self.data_dir, "json/branch_trends.json"), "r") as f:
                self.branch_trends = json.load(f)

            # cutoffs.json and seats.json are now in SQLite
                
            logger.info(f"Loaded {len(self.colleges)} colleges from JSON")
            
            # Merge precise geo-locations
            if self.college_locations:
                updated_count = 0
                for college in self.colleges:
                    code = str(college.get('code'))
                    if code in self.college_locations:
                        geo_data = self.college_locations[code].get('location', {})
                        if geo_data.get('lat') and geo_data.get('lon'):
                            try:
                                college['lat'] = float(geo_data['lat'])
                                college['lng'] = float(geo_data['lon'])
                                updated_count += 1
                            except (ValueError, TypeError):
                                pass
                logger.info(f"Updated geo-locations for {updated_count} colleges")
                
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
        """Retrieves cutoff data for a college from SQLite."""
        if not self.conn:
            return []
        
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM cutoffs WHERE college_code = ?", (college_code,))
            rows = cursor.fetchall()
            
            results = []
            for row in rows:
                r = dict(row)
                # Reconstruct nested structure for compatibility
                cutoffs = {
                    'OC': r['oc'], 'BC': r['bc'], 'BCM': r['bcm'], 'MBC': r['mbc'], 
                    'SC': r['sc'], 'SCA': r['sca'], 'ST': r['st']
                }
                ranks = {
                    'OC': r['oc_rank'], 'BC': r['bc_rank'], 'BCM': r['bcm_rank'], 'MBC': r['mbc_rank'], 
                    'SC': r['sc_rank'], 'SCA': r['sca_rank'], 'ST': r['st_rank']
                }
                results.append({
                    'college_code': r['college_code'],
                    'college_name': r['college_name'],
                    'branch_code': r['branch_code'],
                    'branch_name': r['branch_name'],
                    'year': r['year'],
                    'district': r['district'],
                    'cutoffs': cutoffs,
                    'ranks': ranks
                })
            return results
        except Exception as e:
            logger.error(f"DB Error get_college_cutoffs: {e}")
            return []

    def get_cutoffs_by_branch(self, branch_code: str) -> List[Dict]:
        """Retrieves all cutoff records for a specific branch."""
        if not self.conn:
            return []
            
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM cutoffs WHERE branch_code = ?", (branch_code,))
            rows = cursor.fetchall()
            
            results = []
            for row in rows:
                r = dict(row)
                cutoffs = {
                    'OC': r['oc'], 'BC': r['bc'], 'BCM': r['bcm'], 'MBC': r['mbc'], 
                    'SC': r['sc'], 'SCA': r['sca'], 'ST': r['st']
                }
                results.append({
                    'college_code': r['college_code'],
                    'branch_code': r['branch_code'],
                    'branch_name': r['branch_name'],
                    'year': r['year'],
                    'cutoffs': cutoffs
                })
            return results
        except Exception as e:
            logger.error(f"DB Error get_cutoffs_by_branch: {e}")
            return []

    def get_total_seats_for_college(self, college_code: str, branch_code: str = None) -> int:
        """Retrieves total seats for a college (sum of all branches) or specific branch."""
        if not self.conn:
            return 0
            
        try:
            cursor = self.conn.cursor()
            if branch_code:
                cursor.execute("SELECT total FROM seats WHERE college_code = ? AND branch_code = ?", (college_code, branch_code))
                row = cursor.fetchone()
                return row['total'] if row else 0
            else:
                cursor.execute("SELECT SUM(total) as total_seats FROM seats WHERE college_code = ?", (college_code,))
                row = cursor.fetchone()
                return row['total_seats'] if row and row['total_seats'] else 0
        except Exception as e:
            logger.error(f"DB Error get_seats: {e}")
            return 0

    def get_guidelines(self) -> str:
        """Returns the TNEA guidelines text."""
        return self.guidelines

    def get_yearly_cutoff_stats(self, branch_code: str) -> Dict[int, Dict[str, float]]:
        """
        Returns stats (avg, max, min) for a branch per year.
        Used for Trend Charts.
        """
        if not self.conn:
            return {}
        
        try:
            cursor = self.conn.cursor()
            query = """
                SELECT year, AVG(oc) as avg_cutoff, MAX(oc) as max_cutoff, MIN(oc) as min_cutoff
                FROM cutoffs 
                WHERE branch_code = ? AND oc IS NOT NULL
                GROUP BY year
                ORDER BY year
            """
            cursor.execute(query, (branch_code,))
            rows = cursor.fetchall()
            
            stats = {}
            for r in rows:
                stats[r['year']] = {
                    'avg': round(r['avg_cutoff'], 2),
                    'max': r['max_cutoff'],
                    'min': r['min_cutoff']
                }
            return stats
        except Exception as e:
            logger.error(f"Error getting yearly stats for {branch_code}: {e}")
            return {}

    def get_district_stats(self) -> Dict[str, int]:
        """Returns college count per district."""
        stats = {}
        for c in self.colleges:
            d = c.get('district', 'Unknown')
            stats[d] = stats.get(d, 0) + 1
        # Sort by count desc
        return dict(sorted(stats.items(), key=lambda item: item[1], reverse=True))

if __name__ == "__main__":
    engine = DataEngine()
    logger.info(f"Loaded {len(engine.colleges)} colleges.")
    logger.info(f"Loaded {len(engine.branches)} branches.")
    if engine.percentile_ranges is not None and not engine.percentile_ranges.empty:
        logger.info("Percentile data loaded.")
