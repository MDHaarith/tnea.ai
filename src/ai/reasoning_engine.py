from typing import Dict, Any, List
from ai.prompts import (
    COLLEGE_SUGGESTION_PROMPT,
    RANK_PREDICTION_PROMPT,
    MANAGEMENT_QUOTA_PROMPT,
    LOCATION_FILTER_PROMPT,
    CHOICE_FILLING_PROMPT,
    TREND_ANALYSIS_PROMPT
)

class ReasoningEngine:
    """
    Converts structured logic outputs into natural language explanations or prompts for the LLM.
    """
    
    def prepare_college_suggestion_prompt(self, user_query: str, suggestions: Dict[str, List[Any]]) -> str:
        """
        Creates a prompt for the LLM to explain the college suggestions.
        """
        safe_count = len(suggestions.get("Safe", []))
        mod_count = len(suggestions.get("Moderate", []))
        amb_count = len(suggestions.get("Ambitious", []))
        
        # Extract top 3 names for context
        safe_str = f"{safe_count} Safe options"
        if safe_count > 0:
             names = ", ".join([c['name'] for c in suggestions.get("Safe", [])[:3]])
             safe_str += f" (Include: {names})"

        mod_str = f"{mod_count} Moderate options"
        if mod_count > 0:
             names = ", ".join([c['name'] for c in suggestions.get("Moderate", [])[:3]])
             mod_str += f" (Include: {names})"

        amb_str = f"{amb_count} Ambitious options"
        if amb_count > 0:
             names = ", ".join([c['name'] for c in suggestions.get("Ambitious", [])[:3]])
             amb_str += f" (Include: {names})"

        data_summary = f"""
User Query: "{user_query}"

Analysis Results:
- {safe_str}
- {mod_str}
- {amb_str}
"""
        return f"{COLLEGE_SUGGESTION_PROMPT}\n\nDATA:\n{data_summary}\n\nExplain the options and strategy to the user."

    def prepare_prediction_explanation_prompt(self, mark: float, percentile: float, rank: int, total_students: int) -> str:
        """
        Creates a prompt to explain prediction results.
        """
        return f"""{RANK_PREDICTION_PROMPT}

DATA:
Marks: {mark}
Predicted Percentile: {percentile}
Predicted Rank: {rank}
Estimated Total Students: {total_students}

Explain what this rank means in the context of TNEA:
1. Is it a competitive score?
2. What tier of colleges (Tier 1/2/3) are likely accessible?
"""

    def prepare_low_mark_suggestion_prompt(self, mark: float, percentile: float, rank: int) -> str:
        """Prompt for low mark scenarios - emphasizes honesty and alternatives."""
        return f"""You are an honest TNEA counsellor. A student with LOW marks is asking for help.

DATA:
Marks: {mark}
Percentile: {percentile}
Rank: {rank}

CRITICAL RULES:
- Do NOT give false hope.
- State clearly that options are LIMITED and DIFFICULT.
- Do NOT mention "top colleges" or "guaranteed" outcomes.
- Suggest management quota as a realistic alternative.
- Be empathetic but factual.

Explain their situation honestly."""

    def prepare_management_suggestion_prompt(self, mark: float, eligible_general: bool) -> str:
        """Prompt for management quota fallback."""
        return f"""{MANAGEMENT_QUOTA_PROMPT}

DATA:
Marks: {mark}
Eligible for General Counselling: {eligible_general}

The student is NOT eligible through regular counselling. Explain management quota as an option:
- What is management quota?
- How does it differ from counselling?
- What are the considerations (fees vary by college)?

Do NOT promise easy admission or fixed fees."""

    def prepare_geo_suggestion_prompt(self, rank: int, nearby_colleges: List, radius_km: int) -> str:
        """Prompt for location-based search with no results."""
        return f"""{LOCATION_FILTER_PROMPT}

DATA:
Rank: {rank}
Nearby Colleges Found: {len(nearby_colleges)}
Search Radius: {radius_km} km

SITUATION: NO colleges found in the database within the specified radius.

CRITICAL RULES:
1. Do NOT invent or suggest any college names.
2. You MUST state that no colleges were found in the database.
3. Suggest the student to expand their search radius or consider other areas.
4. Do NOT list IITs, IIMs, or any specific colleges - you have NO data for them.

Response must include:
- Acknowledge no colleges found
- Suggest expanding search radius
- Recommend considering other districts

Do NOT list any college names."""

    def prepare_choice_strategy_prompt(self, rank: int, round_num: int) -> str:
        """Prompt for choice filling strategy."""
        return f"""{CHOICE_FILLING_PROMPT}

DATA:
Rank: {rank}
Round: {round_num}

Explain the choice filling strategy:
1. Safe choices (high chance)
2. Moderate choices (competitive)
3. Ambitious choices (reach goals)

Do NOT say "you will definitely get" any college."""

    def prepare_trend_analysis_prompt(self) -> str:
        """Prompt for trend prediction with missing data."""
        return f"""{TREND_ANALYSIS_PROMPT}

DATA: No exact future data available.

IMPORTANT:
- Future cutoffs CANNOT be predicted exactly.
- Base analysis ONLY on past trends.
- Use probabilistic language ("likely", "may", "historically").
- Do NOT state "the cutoff will be X".

Explain what can and cannot be predicted."""
