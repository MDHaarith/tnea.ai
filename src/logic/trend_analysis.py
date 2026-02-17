import logging
from typing import Dict, List
from data.loader import DataEngine

logger = logging.getLogger("tnea_ai.trends")


class TrendAnalysis:
    def __init__(self):
        self.data_engine = DataEngine()

    def analyze_branch_trend(self, branch_code: str) -> str:
        """
        Analyze year-over-year cutoff trends for a branch using real data.
        Returns a formatted text summary with actual numbers.
        """
        # Collect all cutoff records for this branch across years
        branch_upper = branch_code.upper().strip()
        # Use data engine's filtered query instead of iterating all records
        branch_records = self.data_engine.get_cutoffs_by_branch(branch_upper)
                    
        # Filter further if needed (SQL does strict match, maybe we need fuzzy? SQL works for now)
        # If the SQL returns records, we are good.
        
        
        if not branch_records:
            return f"No historical cutoff data available for branch '{branch_code}'."
        
        # Group by year → collect OC cutoffs
        year_cutoffs: Dict[int, List[float]] = {}
        for r in branch_records:
            year = r.get('year')
            cutoffs = r.get('cutoffs', {})
            oc_cutoff = cutoffs.get('OC')
            if year and oc_cutoff is not None:
                if year not in year_cutoffs:
                    year_cutoffs[year] = []
                year_cutoffs[year].append(float(oc_cutoff))
        
        if not year_cutoffs:
            return f"No OC cutoff data found for branch '{branch_code}'."
        
        # Calculate statistics per year
        years = sorted(year_cutoffs.keys())
        year_stats = {}
        for y in years:
            vals = year_cutoffs[y]
            year_stats[y] = {
                'avg': round(sum(vals) / len(vals), 1),
                'max': round(max(vals), 1),
                'min': round(min(vals), 1),
                'count': len(vals),
            }
        
        # Build summary
        lines = [f"📊 **Trend Analysis: {branch_code.upper()}** ({years[0]}-{years[-1]})\n"]
        lines.append("| Year | Avg Cutoff (OC) | Max | Min | Colleges Offering |")
        lines.append("|------|-----------------|-----|-----|-------------------|")
        for y in years:
            s = year_stats[y]
            lines.append(f"| {y} | {s['avg']} | {s['max']} | {s['min']} | {s['count']} |")
        
        # Year-over-year changes
        if len(years) >= 2:
            lines.append("\n**Year-over-Year Changes:**")
            for i in range(1, len(years)):
                prev_y = years[i-1]
                curr_y = years[i]
                change = year_stats[curr_y]['avg'] - year_stats[prev_y]['avg']
                direction = "📈 Up" if change > 0 else "📉 Down" if change < 0 else "➡️ Flat"
                lines.append(f"- {prev_y} → {curr_y}: {direction} by {abs(change):.1f} marks (avg cutoff)")
            
            # Overall trend
            first_avg = year_stats[years[0]]['avg']
            last_avg = year_stats[years[-1]]['avg']
            total_change = last_avg - first_avg
            college_change = year_stats[years[-1]]['count'] - year_stats[years[0]]['count']
            
            lines.append(f"\n**Overall Trend ({years[0]}-{years[-1]}):**")
            if total_change > 2:
                lines.append(f"- 📈 Cutoffs have **risen** by {total_change:.1f} marks — demand is **increasing**.")
            elif total_change < -2:
                lines.append(f"- 📉 Cutoffs have **dropped** by {abs(total_change):.1f} marks — demand may be **decreasing**.")
            else:
                lines.append(f"- ➡️ Cutoffs have remained **relatively stable** (change of {total_change:.1f} marks).")
            
            if college_change > 0:
                lines.append(f"- {college_change} more colleges now offer this branch compared to {years[0]}.")
            elif college_change < 0:
                lines.append(f"- {abs(college_change)} fewer colleges offer this branch compared to {years[0]}.")
        
        return "\n".join(lines)

    def get_rising_branches(self, top_n: int = 5) -> str:
        """Identify branches with the biggest cutoff increases."""
        if not self.data_engine.conn:
            return "Trend data unavailable."
            
        try:
            cursor = self.data_engine.conn.cursor()
            query = """
                SELECT branch_code, year, AVG(oc) as avg_cutoff 
                FROM cutoffs 
                WHERE oc IS NOT NULL 
                GROUP BY branch_code, year
            """
            cursor.execute(query)
            rows = cursor.fetchall()
            
            branch_changes = {}
            for r in rows:
                bc = r['branch_code']
                year = r['year']
                avg = r['avg_cutoff']
                
                if bc not in branch_changes:
                    branch_changes[bc] = {}
                branch_changes[bc][year] = avg
                
            trends = []
            for bc, year_data in branch_changes.items():
                years = sorted(year_data.keys())
                if len(years) >= 2:
                    first_avg = year_data[years[0]]
                    last_avg = year_data[years[-1]]
                    trends.append((bc, last_avg - first_avg, last_avg))
            
            trends.sort(key=lambda x: x[1], reverse=True)
            
            lines = ["📈 **Rising Demand Branches (Biggest Cutoff Increase):**"]
            for bc, change, latest in trends[:top_n]:
                lines.append(f"- **{bc}**: +{change:.1f} marks (latest avg: {latest:.1f})")
            
            lines.append("\n📉 **Declining Demand Branches:**")
            for bc, change, latest in trends[-top_n:]:
                lines.append(f"- **{bc}**: {change:.1f} marks (latest avg: {latest:.1f})")
            
            return "\n".join(lines)
            
        except Exception as e:
            logger.error(f"Error in get_rising_branches: {e}")
            return "Error calculating trends."
