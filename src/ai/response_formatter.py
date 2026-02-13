import logging
from typing import List, Dict, Any

logger = logging.getLogger("tnea_ai.formatter")


class ResponseFormatter:
    """Formats structured data into Markdown for user display."""
    
    def format_college_list(self, categorized_colleges: Dict[str, List[Dict]], user_mark: float = None) -> str:
        """
        Formats categorized colleges into a markdown table.
        Shows ALL branches per college sorted by relevance.
        Includes placement data and seat count from DB.
        """
        output = []
        
        for category, colleges in categorized_colleges.items():
            if not colleges:
                continue
            
            if category == "Safe":
                sorted_colleges = sorted(colleges, key=lambda c: c.get('cutoff_mark', 0), reverse=True)
            elif category == "Ambitious":
                sorted_colleges = sorted(colleges, key=lambda c: c.get('cutoff_mark', 999))
            else:
                if user_mark:
                    sorted_colleges = sorted(colleges, key=lambda c: abs(c.get('cutoff_mark', 0) - user_mark))
                else:
                    sorted_colleges = sorted(colleges, key=lambda c: c.get('cutoff_mark', 0), reverse=True)
            
            college_groups = {}
            for c in sorted_colleges:
                code = c.get('code')
                if code not in college_groups:
                    college_groups[code] = []
                college_groups[code].append(c)
            
            unique_codes = list(college_groups.keys())[:10]
            remaining = len(college_groups) - 10 if len(college_groups) > 10 else 0

            output.append(f"### {category} Choices ({len(college_groups)} colleges, showing top 10)")
            header = "| # | College Name | Branch | Cutoff | Seats | Placement | District |"
            separator = "|---|---|---|---|---|---|---|"
            output.append(header)
            output.append(separator)
            
            row_num = 1
            for code in unique_codes:
                entries = college_groups[code]
                for i, c in enumerate(entries):
                    name = c.get('name', 'Unknown')
                    if len(name) > 55:
                        name = name[:52] + "..."
                    branch = c.get('branch_name', 'N/A')
                    cutoff = c.get('cutoff_mark', 'N/A')
                    placement = c.get('placement', 'No Data')
                    if placement in (None, 'N/A', 'No_Data', '-', ''):
                        placement = '📊 No Data'
                    location = c.get('district', 'Unknown')
                    seats = c.get('total_seats')
                    seats_str = str(seats) if seats else '—'
                    
                    if i == 0:
                        output.append(f"| {row_num} | **{name}** | {branch} | {cutoff} | {seats_str} | {placement} | {location} |")
                        row_num += 1
                    else:
                        output.append(f"|  | | {branch} | {cutoff} | {seats_str} | {placement} | {location} |")
            
            if remaining > 0:
                output.append(f"*+{remaining} more colleges available.*")
            
            output.append("\n")
            
        return "\n".join(output)

    def format_trend_data(self, trend_text: str) -> str:
        """Formats trend analysis text."""
        return f"**Trend Analysis**:\n\n{trend_text}"
