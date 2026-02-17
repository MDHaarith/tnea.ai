import json
import logging
import difflib
from typing import Generator

from data.loader import DataEngine
from logic.rank_predictor import Predictor
from logic.geo_locator import GeoLocator
from logic.choice_strategy import ChoiceStrategy
from logic.trend_analysis import TrendAnalysis

from ai.reasoning_engine import ReasoningEngine
from ai.response_formatter import ResponseFormatter

from agent.intent_router import IntentRouter
from agent.session_memory import SessionMemory
from llm_gateway import LLMClient
from web.skill_search import SkillSearch
from web.career_mapping import CareerMapper
from ai.prompts import MASTER_SYSTEM_PROMPT
from utils.validators import validate_mark

logger = logging.getLogger("tnea_ai.agent")


def _safe_float(value, default=None):
    """Safely convert a value to float. Returns default if conversion fails."""
    if value is None:
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


class CounsellorAgent:
    def __init__(self, memory=None):
        # Data & Logic
        self.data_engine = DataEngine()
        self.predictor = Predictor(self.data_engine)
        self.geo_locator = GeoLocator()
        self.choice_strategy = ChoiceStrategy()
        self.trend_analysis = TrendAnalysis()
        
        # Web / Skills
        self.skill_search = SkillSearch()
        self.career_mapper = CareerMapper()
        
        # AI
        self.reasoning = ReasoningEngine()
        self.formatter = ResponseFormatter()
        self.llm = LLMClient()
        
        # Agent
        self.intent_router = IntentRouter()
        self.memory = memory if memory is not None else SessionMemory()
        
    def process_query_stream(self, user_query: str) -> Generator[str, None, None]:
        """Main orchestration loop."""
        # 1. Update Memory
        self.memory.add_message("user", user_query)
        
        # 2. Identify Intent
        intent, entities = self.intent_router.route_query(
            user_query, 
            history=self.memory.history, 
            user_profile=self.memory.user_profile
        )
        
        logger.info(f"Intent: {intent}, Entities: {entities}")
        
        # 3. Execute Logic based on Intent
        final_prompt = ""
        system_prompt = MASTER_SYSTEM_PROMPT
        
        if intent == "OFF_TOPIC":
            yield "I'm sorry, but I can only help with TNEA engineering admissions, college counselling, rank predictions, and career guidance. If you have questions about engineering colleges in Tamil Nadu, cutoffs, or the counselling process, I'd be happy to assist!"
            return
        
        if intent == "GREETING":
            greeting_prompt = f"User said: '{user_query}'. Respond with a warm, brief, and professional greeting as TNEA AI. Do not be repetitive. Ask how you can help with engineering admissions."
            final_prompt = greeting_prompt

        elif intent == "PREDICT_PERCENTILE":
            mark = _safe_float(entities.get("mark"))
            if mark is not None and validate_mark(mark):
                self.memory.update_profile("mark", mark)
                p = self.predictor.predict_percentile(mark)
                r = self.predictor.predict_rank(p)
                total = self.predictor.predict_total_students()
                
                self.memory.update_profile("percentile", p)
                self.memory.update_profile("rank", r)
                
                final_prompt = self.reasoning.prepare_prediction_explanation_prompt(mark, p, r, total)
            else:
                yield "Could you please specify a valid cutoff mark (0-200) so I can predict your percentile?"
                return

        elif intent == "SUGGEST_COLLEGES":
            # Check if user is asking about a specific college (Info Query) vs General Recommendation
            college_name_input = entities.get("college_name")
            
            # Resolve college name if provided
            college_name = None
            if college_name_input:
                college_name = self._resolve_college_name(college_name_input)
            
            user_mark = _safe_float(entities.get("mark")) or _safe_float(self.memory.user_profile.get("mark"))
            
            # If specific college request but no mark, JUST return college info (don't block)
            if college_name_input and (user_mark is None or not validate_mark(user_mark)):
                # If resolution failed, try using input directly or notify user
                search_name = college_name or college_name_input
                college_name_upper = search_name.upper()
                
                nearby_colleges = [
                    c for c in self.data_engine.colleges 
                    if college_name_upper in c.get('name', '').upper()
                ]
                
                if not nearby_colleges and college_name:
                     # Try again with raw input if resolved name yielded nothing
                     nearby_colleges = [
                        c for c in self.data_engine.colleges 
                        if college_name_input.upper() in c.get('name', '').upper()
                    ]

                if not nearby_colleges:
                     yield f"I couldn't find a college matching '{college_name_input}' (Resolved: {college_name or 'N/A'}). Could you check the spelling?"
                     return
                
                # Show details for found colleges
                yield f"**Found {len(nearby_colleges)} college(s) matching '{college_name_input}':**\n\n"
                for c in nearby_colleges[:3]: # Limit to top 3 matches
                    yield f"**{c.get('name')}**\n"
                    yield f"- 📍 Location: {c.get('district')}\n"
                    if c.get('placement') and c.get('placement') not in ['N/A', 'No Data']:
                         yield f"- 💼 Placement: {c.get('placement')}\n"
                    
                    # Show cutoffs if available (using 2024 data as generic ref)
                    code = str(c.get('code'))
                    cutoffs = self.data_engine.get_college_cutoffs(code)
                    if cutoffs:
                        yield "- 📉 **Past Cutoffs (OC)**: "
                        # Get latest year cutoffs for a few branches
                        latest_year = max([x.get('year',0) for x in cutoffs]) if cutoffs else 0
                        relevant = [x for x in cutoffs if x.get('year') == latest_year][:3]
                        cutoff_strs = [f"{x.get('branch_code')}: {x.get('cutoffs',{}).get('OC','N/A')}" for x in relevant]
                        yield ", ".join(cutoff_strs) + " ...\n"
                    yield "\n"
                
                yield "\n*To get your specific admission probability, please tell me your cutoff mark.*"
                return

            # If Location-based query but no mark, JUST return colleges in that location (don't block)
            location_input = entities.get("location")
            if location_input and (user_mark is None or not validate_mark(user_mark)):
                 nearby = self.geo_locator.find_nearby_colleges(location_input)
                 if not nearby:
                     # Fallback to string match if geo fails
                     nearby = [c for c in self.data_engine.colleges if location_input.upper() in c.get('district','').upper()]

                 if not nearby:
                     yield f"I couldn't find any engineering colleges in or near '{location_input}'."
                     return
                 
                 yield f"**Found {len(nearby)} colleges near '{location_input}':**\n\n"
                 # Show top 5
                 for c in nearby[:5]:
                    dist_str = f" (~{c.get('_distance_km')} km away)" if c.get('_distance_km') else ""
                    yield f"**{c.get('name')}**{dist_str}\n"
                    yield f"- 📍 {c.get('district', 'Unknown')}\n"
                    if c.get('placement') and c.get('placement') not in ['N/A', 'No Data']:
                         yield f"- 💼 Placement: {c.get('placement')}\n"
                    yield "\n"
                 
                 if len(nearby) > 5:
                     yield f"*...and {len(nearby)-5} more.*\n"

                 yield "\n*To see which of these you can likely get into, please tell me your cutoff mark.*"
                 return

            if user_mark is None or not validate_mark(user_mark):
                yield "I need to know your cutoff marks (0-200) to suggest colleges. What is your score?"
                return
            self.memory.update_profile("mark", user_mark)
            
            location = entities.get("location") or self.memory.user_profile.get("preferred_location")
            if entities.get("location"):
                self.memory.update_profile("preferred_location", entities["location"])
            
            branch = entities.get("branch") or self.memory.user_profile.get("preferred_branch")
            if entities.get("branch"):
                self.memory.update_profile("preferred_branch", entities["branch"])
                
            community = entities.get("community") or self.memory.user_profile.get("community", "OC")
            if entities.get("community"):
                self.memory.update_profile("community", entities["community"])
            
            
            if location:
                nearby_colleges = self.geo_locator.find_nearby_colleges(location)
            else:
                nearby_colleges = self.data_engine.colleges
            if not nearby_colleges:
                nearby_colleges = self.data_engine.colleges
            
            if college_name:
                # Use the resolved name
                college_name_upper = college_name.upper()
                nearby_colleges = [
                    c for c in nearby_colleges 
                    if college_name_upper in c.get('name', '').upper()
                ]
                # Fallback to broad search if strict filter failed
                if not nearby_colleges:
                     nearby_colleges = [
                        c for c in self.data_engine.colleges 
                        if college_name_upper in c.get('name', '').upper()
                    ]
            
            enriched = self._enrich_with_cutoffs(nearby_colleges, community.upper())
            
            if branch:
                enriched = self._filter_by_branch(enriched, branch)
            
            if not enriched:
                yield f"No colleges found matching your criteria (College: {college_name or 'Any'}, Branch: {branch or 'Any'}, Location: {location or 'All TN'}, Cutoff: {user_mark}). Try broadening your search."
                return
            
            user_mark_f = float(user_mark)
            predicted_pct = self.predictor.predict_percentile(user_mark_f)
            predicted_rank = self.predictor.predict_rank(predicted_pct)
            predicted_total = self.predictor.predict_total_students()
            
            self.memory.update_profile("percentile", predicted_pct)
            self.memory.update_profile("rank", predicted_rank)
            
            # Removed repetitive "Your Profile" template. This info is now in context.
            
            categorized = self.choice_strategy.categorize_options(user_mark_f, enriched)
            
            formatted_data = self.formatter.format_college_list(categorized, user_mark=user_mark_f)
            yield formatted_data + "\n\n"
            
            final_prompt = self._build_grounded_college_prompt(
                user_query, user_mark_f, categorized, location, branch,
                predicted_rank, predicted_pct, predicted_total
            )

        elif intent == "CHOICE_FILLING":
            user_mark = _safe_float(entities.get("mark")) or _safe_float(self.memory.user_profile.get("mark"))
            if user_mark is None or not validate_mark(user_mark):
                yield "I need your cutoff mark (0-200) to generate a choice-filling table. What is your score?"
                return
            
            user_mark_f = float(user_mark)
            branch = entities.get("branch") or self.memory.user_profile.get("preferred_branch")
            location = entities.get("location") or self.memory.user_profile.get("preferred_location")
            community = entities.get("community") or self.memory.user_profile.get("community", "OC")
            
            predicted_pct = self.predictor.predict_percentile(user_mark_f)
            predicted_rank = self.predictor.predict_rank(predicted_pct)
            predicted_total = self.predictor.predict_total_students()
            
            yield f"📊 **Your Profile**: Cutoff **{user_mark_f}** → Percentile **{predicted_pct}** → Rank **~{predicted_rank}** (out of ~{predicted_total})\n\n"
            yield f"📋 **Generating your choice-filling priority table...**\n\n"
            
            if location:
                nearby = self.geo_locator.find_nearby_colleges(location)
                if not nearby:
                    nearby = self.data_engine.colleges
            else:
                nearby = self.data_engine.colleges
            
            enriched = self._enrich_with_cutoffs(nearby, community.upper())
            
            if branch:
                enriched = self._filter_by_branch(enriched, branch)
            
            if not enriched:
                yield "No eligible colleges found. Try broadening your branch or location preferences."
                return
            
            categorized = self.choice_strategy.categorize_options(user_mark_f, enriched)
            
            formatted = self.formatter.format_college_list(categorized, user_mark=user_mark_f)
            yield formatted + "\n\n"
            
            branch_str = f" for {branch} branch" if branch else ""
            location_str = f" in {location}" if location else ""
            
            safe_count = len(categorized.get("Safe", []))
            mod_count = len(categorized.get("Moderate", []))
            amb_count = len(categorized.get("Ambitious", []))
            
            final_prompt = f"""Generate a COMPLETE CHOICE-FILLING PRIORITY TABLE for this TNEA student.

Student Profile:
- Cutoff Mark: {user_mark_f}
- Predicted Rank: ~{predicted_rank}
- Percentile: {predicted_pct}
- Preferred Branch: {branch or 'All branches'}
- Location: {location or 'All Tamil Nadu'}
- Community: {community}
- Total eligible: {safe_count} Safe + {mod_count} Moderate + {amb_count} Ambitious colleges

DATA AVAILABLE:
{formatted}

GENERATE THE FOLLOWING:

1. **CHOICE-FILLING PRIORITY TABLE** with 20-25 choices in recommended filling order:
   | Priority | College Name | Branch | Cutoff | Placement (from DB) | Category | Strategy |
   Include a mix: 3-4 Ambitious (dream picks), 8-10 Moderate (realistic targets), 8-10 Safe (backup/guaranteed).
   For the Placement column: ONLY use the exact placement % from the DATA AVAILABLE section above. If the data says "No Data" or "📊 No Data", write "Not verified" — NEVER make up placement percentages or salary figures.

2. **FILLING STRATEGY**: 
   - Why this specific order matters
   - How sliding admission works (if you get allotted a lower choice, you can slide up in later rounds)
   - When to use "Float" vs "Freeze" options

3. **KEY TIPS**:
   - What to do if you don't get allotted in Round 1
   - Management quota vs counselling trade-offs
   - Branch priority vs college tier trade-offs

4. **PLACEMENT NOTE**: Only quote placement data from the table above. If placement data says "No Data", say "Not verified — check the official college website." DO NOT fabricate placement percentages, salary ranges, or recruiter names.

Be comprehensive and detailed. This table will be used by the student for actual TNEA choice filling. Use ONLY the exact data provided — never invent cutoff numbers, college names, or placement statistics.
"""

        elif intent == "CAREER_PLANNING":
            response = self.career_mapper.map_career(user_query)
            final_prompt = f"User asked about career: {user_query}\n\nAI Analysis:\n{response}\n\nSummarize and guide the student."

        elif intent == "SKILL_GUIDANCE":
            response = self.skill_search.search_skills(user_query)
            final_prompt = f"User asked about skills: {user_query}\n\nAI Analysis:\n{response}\n\nProvide a skill roadmap."

        elif intent == "TREND_ANALYSIS":
            # Use the real trend analysis engine
            branch = entities.get("branch")
            if branch:
                trend_data = self.trend_analysis.analyze_branch_trend(branch)
                yield trend_data + "\n\n"
                final_prompt = f"User asked for trends: {user_query}\n\nHere is the real trend data:\n{trend_data}\n\nProvide additional insights and interpretation of these trends. What do they mean for a student considering this branch? Use ONLY the data provided above."
            else:
                # General trend overview
                rising = self.trend_analysis.get_rising_branches()
                yield rising + "\n\n"
                final_prompt = f"User asked for trends: {user_query}\n\nHere is the trend overview:\n{rising}\n\nProvide insights on which branches are growing and which are declining. Advise the student based on this data."
            
        else:  # GENERAL_QUERY or GUIDANCE
            guidelines = self.data_engine.get_guidelines()[:2000]
            final_prompt = f"User Query: {user_query}\n\nContext (TNEA Guidelines): {guidelines}\n\nAnswer the user."

        # 4. Stream LLM Response
        if final_prompt:
            stream = self.llm.generate_response(final_prompt, system_prompt=system_prompt, stream=True)
            full_response = ""
            for chunk, _ in stream:
                 full_response += chunk
                 yield chunk
            
            # 5. Save Agent Response to memory
            self.memory.add_message("assistant", full_response)
            
            # 6. Disclaimer (Reduced)
            yield "\n\n<span style='font-size:0.8em; color:gray'>Note: Cutoff data from official TNEA records. Predictions are AI estimates. Verify with colleges.</span>"

    # Branch alias mapping
    BRANCH_ALIASES = {
        "ECE": ["ELECTRONICS AND COMMUNICATION"],
        "CSE": ["COMPUTER SCIENCE AND ENGINEERING"],
        "MECH": ["MECHANICAL ENGINEERING"],
        "CIVIL": ["CIVIL ENGINEERING"],
        "EEE": ["ELECTRICAL AND ELECTRONICS"],
        "IT": ["INFORMATION TECHNOLOGY"],
        "AI": ["ARTIFICIAL INTELLIGENCE"],
        "AIDS": ["ARTIFICIAL INTELLIGENCE AND DATA SCIENCE"],
        "AIML": ["AI AND MACHINE LEARNING"],
        "BME": ["BIO MEDICAL ENGINEERING", "BIOMEDICAL"],
        "CHEM": ["CHEMICAL ENGINEERING"],
        "AUTO": ["AUTOMOBILE ENGINEERING"],
        "AERO": ["AERONAUTICAL ENGINEERING"],
        "BIOTECH": ["BIO TECHNOLOGY", "BIOTECHNOLOGY"],
        "CSBS": ["COMPUTER SCIENCE AND BUSSINESS SYSTEM", "COMPUTER SCIENCE AND BUSINESS"],
        "CSD": ["COMPUTER SCIENCE AND DESIGN"],
        "FOOD": ["FOOD TECHNOLOGY"],
        "AGRI": ["AGRICULTURAL ENGINEERING"],
        "MARINE": ["MARINE ENGINEERING"],
        "MINING": ["MINING ENGINEERING"],
        "TEXTILE": ["TEXTILE TECHNOLOGY"],
        "PRINTING": ["PRINTING"],
        "ROBOTICS": ["ROBOTICS"],
        "CYBER": ["CYBER SECURITY"],
        "IOT": ["INTERNET OF THINGS"],
        "MECHATRONICS": ["MECHATRONICS"],
        "CORE": ["ELECTRONICS AND COMMUNICATION", "ELECTRICAL AND ELECTRONICS", "MECHANICAL ENGINEERING", "CIVIL ENGINEERING"],
        "CS GROUP": ["COMPUTER SCIENCE", "INFORMATION TECHNOLOGY", "ARTIFICIAL INTELLIGENCE", "CYBER", "DATA SCIENCE", "COMPUTING", "MACHINE LEARNING", "IOT"],
        "CS": ["COMPUTER SCIENCE", "INFORMATION TECHNOLOGY", "ARTIFICIAL INTELLIGENCE", "CYBER", "DATA SCIENCE", "COMPUTING", "MACHINE LEARNING", "IOT"],
    }

    def _enrich_with_cutoffs(self, colleges: list, community: str = "OC") -> list:
        """Enrich college list with cutoff and seat data. Only keeps latest year per college+branch."""
        enriched = []
        for c in colleges:
            code = c.get('code')
            college_cutoffs = self.data_engine.get_college_cutoffs(str(code))
            if not college_cutoffs:
                continue
            
            # Group by branch, keep latest year only
            branch_latest = {}
            for bc in college_cutoffs:
                branch_key = bc.get('branch_code', '') or bc.get('branch_name', '')
                year = bc.get('year', 0)
                if branch_key not in branch_latest or year > branch_latest[branch_key].get('year', 0):
                    branch_latest[branch_key] = bc
            
            for branch_key, bc in branch_latest.items():
                cutoffs = bc.get('cutoffs', {})
                cutoff_val = cutoffs.get(community) or cutoffs.get('OC')
                if cutoff_val is not None:
                    # Get seat count
                    total_seats = self.data_engine.get_total_seats_for_college(
                        str(code), bc.get('branch_code', '')
                    )
                    
                    enriched.append({
                        'code': code,
                        'name': c.get('name', 'Unknown'),
                        'district': c.get('district', 'Unknown'),
                        'branch_name': bc.get('branch_name', 'Unknown'),
                        'branch_code': bc.get('branch_code', ''),
                        'cutoff_mark': float(cutoff_val),
                        'placement': c.get('placement', 'N/A'),
                        'year': bc.get('year', 'N/A'),
                        'total_seats': total_seats if total_seats > 0 else None,
                    })
        return enriched

    def _filter_by_branch(self, enriched: list, branch_query: str) -> list:
        """Filter enriched colleges by branch using alias mapping and substring matching."""
        branch_upper = branch_query.upper().strip()
        keywords = self.BRANCH_ALIASES.get(branch_upper)
        if not keywords:
            keywords = [branch_upper]
        
        filtered = []
        for entry in enriched:
            bname = entry.get('branch_name', '').upper()
            if any(kw in bname for kw in keywords):
                filtered.append(entry)
        return filtered

    def _build_grounded_college_prompt(self, user_query: str, mark: float, categorized: dict, 
                                        location: str = None, branch: str = None,
                                        rank: int = None, percentile: float = None, total_students: int = None) -> str:
        """Builds a fully data-grounded prompt with rank info and next steps."""
        
        def format_entries(entries, sort_key="cutoff_mark", reverse=True, max_items=10):
            sorted_e = sorted(entries, key=lambda x: x.get(sort_key, 0), reverse=reverse)
            college_groups = {}
            for e in sorted_e:
                key = e.get('code')
                if key not in college_groups:
                    college_groups[key] = []
                college_groups[key].append(e)
            
            lines = []
            for code in list(college_groups.keys())[:max_items]:
                for e in college_groups[code]:
                    placement = e.get('placement', 'No Data')
                    if placement in (None, 'N/A', 'No_Data', '-', ''):
                        placement = 'No Data'
                    seats = e.get('total_seats')
                    seats_str = f" | Seats: {seats}" if seats else ""
                    lines.append(f"- {e['name']} | Branch: {e['branch_name']} | Cutoff: {e['cutoff_mark']} | Placement: {placement}{seats_str} | District: {e['district']}")
            return "\n".join(lines) if lines else "None found."
        
        safe_data = format_entries(categorized.get("Safe", []), reverse=True)
        moderate_data = format_entries(categorized.get("Moderate", []), reverse=True)
        ambitious_data = format_entries(categorized.get("Ambitious", []), reverse=False)
        
        location_str = f" in {location}" if location else " across Tamil Nadu"
        branch_str = f" for {branch} branch" if branch else ""
        rank_str = f"\nStudent Rank: ~{rank} (Percentile: {percentile}, Total Students: ~{total_students})" if rank else ""
        
        return f"""The student asked: "{user_query}"
Student's Cutoff Mark: {mark}{rank_str}
Search: Colleges{location_str}{branch_str}

Below is the REAL data from our TNEA database. You MUST ONLY reference colleges from the data below. NEVER invent colleges, cutoffs, or placement numbers.

=== SAFE CHOICES (Cutoff below student's mark — high admission chance) ===
{safe_data}

=== MODERATE CHOICES (Cutoff close to student's mark — competitive) ===
{moderate_data}

=== AMBITIOUS CHOICES (Cutoff above student's mark — reach goals) ===
{ambitious_data}

INSTRUCTIONS:
1. **Focus on RANK** for context: Start by mentioning their estimated rank (~{rank}) to set expectations. Mention cutoff only as a reference.
2. Present the top 10 best college options from ALL categories above. Prioritize Moderate and Safe choices with the highest cutoffs (most competitive colleges the student can realistically get).
3. For EACH college, mention: college name, ALL eligible branches with cutoffs, placement % from the data (if available), and label it ✅ Safe / ⚖️ Moderate / 🚀 Ambitious.
4. NEVER invent any data. Use EXACT numbers from above.
5. For placement: ONLY quote the placement % shown in the data above. If placement says "No Data", say "Placement: Not verified" — DO NOT make up percentages or salary figures.
6. Keep descriptions to 1-2 lines per college.
7. Avoid repetitive headers like "Based on your cutoff...". Be conversational.

NEXT STEPS (Always include these at the end):
After presenting colleges, suggest 3-4 specific, actionable next steps such as:
- Which documents to prepare for counselling
- Whether to explore specific branches they haven't considered
- How to check placement records for shortlisted colleges  
- When to register for TNEA counselling and key deadlines
- Whether they should consider both government and aided colleges

IMPORTANT: Always end your response with this exact question (on a new line):
"📋 **Would you like me to generate a complete choice-filling priority table with all eligible colleges ranked in recommended order?**"
"""

    def _resolve_college_name(self, college_input: str) -> str:
        """Resolves abbreviations or fuzzy names to full college names."""
        if not college_input:
            return None
            
        college_input = college_input.strip()
        
        # 1. Aliases Map
        ALIASES = {
            "CEG": "COLLEGE OF ENGINEERING GUINDY",
            "GUINDY": "COLLEGE OF ENGINEERING GUINDY",
            "MIT": "MADRAS INSTITUTE OF TECHNOLOGY",
            "SSN": "SSN COLLEGE OF ENGINEERING",
            "KCT": "KUMARAGURU COLLEGE OF TECHNOLOGY",
            "KUMARAGURU": "KUMARAGURU COLLEGE OF TECHNOLOGY",
            "PSG": "PSG COLLEGE OF TECHNOLOGY", # Careful, there's also PSG iTech
            "PSG TECH": "PSG COLLEGE OF TECHNOLOGY",
            "PSG ITECH": "PSG INSTITUTE OF TECHNOLOGY AND APPLIED RESEARCH",
            "SKCET": "SRI KRISHNA COLLEGE OF ENGINEERING AND TECHNOLOGY",
            "REC": "RAJALAKSHMI ENGINEERING COLLEGE",
            "SVCE": "SRI VENKATESWARA COLLEGE OF ENGINEERING",
            "CIT": "COIMBATORE INSTITUTE OF TECHNOLOGY", # Could specify Chennai/Coimbatore? usually CBE
            "GCT": "GOVERNMENT COLLEGE OF TECHNOLOGY",
            "GCE": "GOVERNMENT COLLEGE OF ENGINEERING",
            "SAIRAM": "SRI SAIRAM ENGINEERING COLLEGE",
            "RMK": "R.M.K. ENGINEERING COLLEGE",
            "RMD": "R.M.D. ENGINEERING COLLEGE",
            "ST JOSEPH": "ST. JOSEPH'S COLLEGE OF ENGINEERING",
            "JEPPIAAR": "JEPPIAAR ENGINEERING COLLEGE",
            "LOYOLA": "LOYOLA-ICAM COLLEGE OF ENGINEERING AND TECHNOLOGY",
            "LICET": "LOYOLA-ICAM COLLEGE OF ENGINEERING AND TECHNOLOGY",
            "MEPCO": "MEPCO SCHLENK ENGINEERING COLLEGE",
            "KONGU": "KONGU ENGINEERING COLLEGE",
            "BANNARI": "BANNARI AMMAN INSTITUTE OF TECHNOLOGY",
            "BIT": "BANNARI AMMAN INSTITUTE OF TECHNOLOGY",
            "SONA": "SONA COLLEGE OF TECHNOLOGY",
            "VELAMMAL": "VELAMMAL ENGINEERING COLLEGE",
            "EASWARI": "EASWARI ENGINEERING COLLEGE",
            "PANIMALAR": "PANIMALAR ENGINEERING COLLEGE",
            "SAVITHA": "SAVEETHA ENGINEERING COLLEGE",
            "SAVEETHA": "SAVEETHA ENGINEERING COLLEGE",
        }
        
        upper_input = college_input.upper()
        if upper_input in ALIASES:
            return ALIASES[upper_input]
            
        # 2. Fuzzy Match against known Aliases
        match = difflib.get_close_matches(upper_input, ALIASES.keys(), n=1, cutoff=0.8)
        if match:
            return ALIASES[match[0]]
            
        # 3. Fuzzy match against all known college names in DB
        all_names = [c.get('name', '').upper() for c in self.data_engine.colleges]
        match = difflib.get_close_matches(upper_input, all_names, n=1, cutoff=0.7)
        if match:
            return match[0]

        # 4. LLM Fallback (Simulation of "Web Search" / Reasoning)
        try:
            prompt = f"""Identify the specific Tamil Nadu engineering college referred to by: "{college_input}".
            Return ONLY the full official name of the college. If unsure or if it's not a college, return "UNKNOWN"."""
            
            response, _ = self.llm.generate_response(prompt, max_tokens=50)
            cleaned = response.strip().replace('"', '').replace('.', '')
            if "UNKNOWN" not in cleaned and len(cleaned) > 5:
                 return cleaned
        except Exception:
            pass
            
        return college_input
