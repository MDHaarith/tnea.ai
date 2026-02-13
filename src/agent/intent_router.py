import json
import re
import logging
from typing import Dict, Any, Tuple, List, Optional
from llm_gateway import LLMClient
from ai.prompts import INTENT_ROUTER_PROMPT

logger = logging.getLogger("tnea_ai.router")

# Branch short forms for entity extraction
KNOWN_BRANCHES = [
    "CSE", "ECE", "MECH", "CIVIL", "EEE", "IT", "AI", "AIDS", "AIML",
    "BME", "CHEM", "AUTO", "AERO", "BIOTECH", "CSBS", "CSD", "FOOD",
    "AGRI", "MARINE", "MINING", "TEXTILE", "PRINTING", "ROBOTICS",
    "CYBER", "IOT", "MECHATRONICS", "CORE", "CS GROUP", "CS"
]

# Tamil Nadu districts for location extraction
TN_DISTRICTS = [
    "CHENNAI", "COIMBATORE", "MADURAI", "TIRUCHIRAPPALLI", "TRICHY", "SALEM",
    "TIRUNELVELI", "ERODE", "VELLORE", "THANJAVUR", "DINDIGUL", "KANCHIPURAM",
    "CUDDALORE", "TIRUVANNAMALAI", "VILLUPURAM", "NAGAPATTINAM", "NAMAKKAL",
    "KARUR", "SIVAGANGA", "THENI", "VIRUDHUNAGAR", "RAMANATHAPURAM",
    "THOOTHUKUDI", "TUTICORIN", "PERAMBALUR", "ARIYALUR", "KRISHNAGIRI",
    "DHARMAPURI", "TIRUPPUR", "TIRUPUR", "NILGIRIS", "OOTY", "PUDUKKOTTAI",
    "KANYAKUMARI", "NAGERCOIL", "KALLAKURICHI", "RANIPET", "TIRUPATTUR",
    "CHENGALPATTU", "TENKASI", "MAYILADUTHURAI", "HOSUR", "AMBUR",
]


class IntentRouter:
    """Classifies user queries into specific intents using local rules + AI fallback."""
    
    def __init__(self):
        self.llm = LLMClient()
    
    def route_query(self, query: str, history: list = None, user_profile: dict = None) -> Tuple[str, Dict[str, Any]]:
        """Routes the query. Tries local classification first, falls back to LLM."""
        
        # 1. Try local classification (fast, free)
        local_result = self._local_classify(query, history, user_profile)
        if local_result is not None:
            intent, entities = local_result
            logger.info(f"Local classification: intent={intent}, entities={entities}")
            return intent, entities
        
        # 2. Fall back to LLM classification (slow, costs API)
        logger.info(f"Local classification inconclusive, using LLM for: {query[:80]}")
        try:
            analysis = self.route_with_llm(query, history)
        except Exception as e:
            logger.error(f"LLM Routing Error: {e}")
            return self._fallback_route(query)
        
        if analysis.get("is_off_topic", False):
            return "OFF_TOPIC", {}
        
        intent = analysis.get("intent", "GENERAL_QUERY").upper()
        entities = analysis.get("entities", {})
        
        mapping = {
            "RANK_PREDICTION": "PREDICT_PERCENTILE",
            "COLLEGE_SUGGESTION": "SUGGEST_COLLEGES",
            "LOCATION_FILTER": "SUGGEST_COLLEGES",
            "MANAGEMENT_QUOTA": "CHECK_VACANCY",
            "PROCESS_GUIDANCE": "GUIDANCE",
            "GREETING": "GREETING",
            "CHOICE_FILLING": "CHOICE_FILLING",
            "CAREER_PLANNING": "CAREER_PLANNING",
            "SKILL_GUIDANCE": "SKILL_GUIDANCE",
        }
        
        internal_intent = mapping.get(intent, intent)
        cleaned_entities = {k: v for k, v in entities.items() if v is not None}
        
        college_intents = {"SUGGEST_COLLEGES", "CHOICE_FILLING", "PREDICT_PERCENTILE"}
        if cleaned_entities.get("mark") and internal_intent not in college_intents:
            internal_intent = "PREDICT_PERCENTILE"
            
        if not cleaned_entities.get("mark") and re.match(r'^\d+(\.\d+)?$', query.strip()):
            cleaned_entities["mark"] = float(query.strip())
            internal_intent = "PREDICT_PERCENTILE"

        return internal_intent, cleaned_entities

    def _local_classify(self, query: str, history: list = None, user_profile: dict = None) -> Optional[Tuple[str, Dict[str, Any]]]:
        """
        Fast local intent classification using keywords and regex.
        Returns (intent, entities) if confident, None if ambiguous.
        """
        q = query.strip()
        q_lower = q.lower()
        entities = {}
        
        # --- Entity extraction (always run) ---
        # Extract marks
        mark_match = re.search(r'(?:cutoff|marks?|score|cut off|my)\s*(?:is|are|of|:)?\s*(\d{1,3}(?:\.\d+)?)', q_lower)
        if mark_match:
            mark_val = float(mark_match.group(1))
            if 0 <= mark_val <= 200:
                entities["mark"] = mark_val
        
        # Pure number input
        if re.match(r'^\d{1,3}(\.\d+)?$', q.strip()):
            entities["mark"] = float(q.strip())
            if 0 <= entities["mark"] <= 200:
                return "PREDICT_PERCENTILE", entities
            else:
                entities.pop("mark", None)
        
        # Extract location (district/city)
        for district in TN_DISTRICTS:
            if district.lower() in q_lower:
                entities["location"] = district.title()
                break
        if not entities.get("location"):
            loc_match = re.search(r'(?:in|near|around|at|from)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)', q)
            if loc_match:
                entities["location"] = loc_match.group(1)
        
        # Extract branch
        for branch in KNOWN_BRANCHES:
            if re.search(r'\b' + branch + r'\b', q.upper()):
                entities["branch"] = branch
                break
        # Also check full names
        branch_fullnames = {
            "computer science": "CS", "electronics": "ECE", "mechanical": "MECH",
            "civil": "CIVIL", "electrical": "EEE", "information technology": "IT",
            "artificial intelligence": "AI", "data science": "AIDS",
            "biotechnology": "BIOTECH", "biomedical": "BME",
        }
        for fullname, short in branch_fullnames.items():
            if fullname in q_lower:
                entities["branch"] = short
                break
        
        # Extract community
        community_match = re.search(r'\b(OC|BC|BCM|MBC|SC|SCA|ST)\b', q.upper())
        if community_match:
            entities["community"] = community_match.group(1)
        
        # --- Intent classification ---
        # Greeting (only if short and clearly a greeting)
        greeting_patterns = r'^(hi|hello|hey|good\s*(morning|afternoon|evening|night)|greetings|howdy|sup|yo|vanakkam)\s*[!.,]?\s*$'
        if re.match(greeting_patterns, q_lower):
            return "GREETING", {}
        
        # Off-topic detection
        off_topic_keywords = ["weather", "movie", "song", "cricket", "football", "recipe", "joke", "game", "bitcoin", "stock market"]
        if any(kw in q_lower for kw in off_topic_keywords) and not any(kw in q_lower for kw in ["college", "branch", "tnea", "engineering", "cutoff"]):
            return "OFF_TOPIC", {}
        
        # Score-based classification
        scores = {
            "PREDICT_PERCENTILE": 0,
            "SUGGEST_COLLEGES": 0,
            "CHOICE_FILLING": 0,
            "CAREER_PLANNING": 0,
            "SKILL_GUIDANCE": 0,
            "TREND_ANALYSIS": 0,
            "GUIDANCE": 0,
        }
        
        # Prediction keywords
        pred_kw = ["predict", "rank", "percentile", "what rank", "my rank", "estimate", "expected rank"]
        for kw in pred_kw:
            if kw in q_lower:
                scores["PREDICT_PERCENTILE"] += 2
        if entities.get("mark") and not any(kw in q_lower for kw in ["college", "suggest", "recommend", "choice"]):
            scores["PREDICT_PERCENTILE"] += 3
        
        # College suggestion keywords
        college_kw = ["college", "suggest", "recommend", "best", "top", "which college", "list college", "available college", "options"]
        for kw in college_kw:
            if kw in q_lower:
                scores["SUGGEST_COLLEGES"] += 2
        if entities.get("location"):
            scores["SUGGEST_COLLEGES"] += 1
        
        # Choice filling keywords
        choice_kw = ["choice fill", "choice list", "priority", "order of", "filling order", "how to fill", "choice table"]
        for kw in choice_kw:
            if kw in q_lower:
                scores["CHOICE_FILLING"] += 3
        
        # Career keywords
        career_kw = ["career", "job", "scope", "future", "salary", "placement", "industry", "work", "opportunities"]
        for kw in career_kw:
            if kw in q_lower:
                scores["CAREER_PLANNING"] += 2
        
        # Skill keywords
        skill_kw = ["skill", "learn", "course", "certification", "roadmap", "prepare", "study"]
        for kw in skill_kw:
            if kw in q_lower:
                scores["SKILL_GUIDANCE"] += 2
        
        # Trend keywords
        trend_kw = ["trend", "historical", "year over year", "compare", "increasing", "decreasing", "demand"]
        for kw in trend_kw:
            if kw in q_lower:
                scores["TREND_ANALYSIS"] += 2
        
        # Process/guidance keywords
        proc_kw = ["process", "registration", "document", "certificate", "how to apply", "counselling process", "steps", "eligibility", "round"]
        for kw in proc_kw:
            if kw in q_lower:
                scores["GUIDANCE"] += 2
        
        # Find the winner
        max_score = max(scores.values())
        if max_score >= 3:
            # Clear winner — confident enough to skip LLM
            winners = [k for k, v in scores.items() if v == max_score]
            if len(winners) == 1:
                return winners[0], entities
            # If tied between college suggestion and prediction with mark + location
            if "SUGGEST_COLLEGES" in winners and entities.get("location"):
                return "SUGGEST_COLLEGES", entities
            if "PREDICT_PERCENTILE" in winners and entities.get("mark"):
                return "PREDICT_PERCENTILE", entities
            # Still tied — return first winner
            return winners[0], entities
        
        # Not confident enough — let LLM handle it
        return None

    def extract_json(self, text: str) -> dict:
        """Robustly extracts JSON from LLM output."""
        text = text.strip()
        
        if "```json" in text:
            pattern = r"```json\s*(.*?)\s*```"
            match = re.search(pattern, text, re.DOTALL)
            if match:
                text = match.group(1)
        elif "```" in text:
            pattern = r"```\s*(.*?)\s*```"
            match = re.search(pattern, text, re.DOTALL)
            if match:
                text = match.group(1)
        
        start = text.find('{')
        end = text.rfind('}')
        
        if start != -1 and end != -1:
            json_str = text[start:end+1]
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                pass
        
        raise ValueError("No valid JSON found in response")

    def route_with_llm(self, query: str, history: list = None) -> dict:
        """Uses LLM to classify intent."""
        context = ""
        if history:
            context = "\n".join([f"{m['role']}: {m['content']}" for m in history[-3:]])
        
        prompt = f"""### History:
{context}

### User Query:
{query}

Analyze the query and provide the JSON output as specified in system instructions.
Ensure strict JSON format."""
        
        response, _ = self.llm.generate_response(prompt, system_prompt=INTENT_ROUTER_PROMPT)
        return self.extract_json(response)

    def _fallback_route(self, query: str) -> Tuple[str, Dict[str, Any]]:
        """Simple keyword-based routing when everything else fails."""
        q = query.lower()
        if any(w in q for w in ["hi", "hello", "hey"]):
            return "GREETING", {}
        if any(w in q for w in ["predict", "rank", "percentile", "cutoff"]):
            return "PREDICT_PERCENTILE", {}
        if any(w in q for w in ["college", "suggest", "recommend", "best"]):
            return "SUGGEST_COLLEGES", {}
        return "GENERAL_QUERY", {}
