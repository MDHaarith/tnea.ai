import json
import os
import sys

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from agent.intent_router import IntentRouter
from ai.reasoning_engine import ReasoningEngine
from ai.prompts import MASTER_SYSTEM_PROMPT

from llm_gateway import LLMClient

def run_tests():
    print("Loading Test Cases...")
    with open(os.path.join(os.path.dirname(__file__), 'test_cases.json'), 'r') as f:
        test_cases = json.load(f)
    
    router = IntentRouter()
    reasoning = ReasoningEngine()
    llm = LLMClient() 
    
    passed = 0
    failed = 0
    
    print(f"\nRunning {len(test_cases)} Tests...\n")
    
    for case in test_cases:
        print(f"Test [{case['id']}]: ", end="")
        sys.stdout.flush() # Ensure print appears before slow LLM call
        
        try:
            if case['type'] == 'intent':
                intent, _ = router.route_query(case['input'])
                # Allow mapped intents or direct matches
                if intent == case['expected_intent']:
                    print("PASS")
                    passed += 1
                else:
                    print(f"FAIL (Expected {case['expected_intent']}, got {intent})")
                    failed += 1
                    
            elif case['type'] == 'reasoning':
                # Generate prompt based on type
                ctx = case.get('context', {})
                prompt_type = case['prompt_type']
                
                if prompt_type == 'prediction_explanation':
                    prompt = reasoning.prepare_prediction_explanation_prompt(
                        ctx['mark'], ctx['percentile'], ctx['rank'], ctx['total_students']
                    )
                elif prompt_type == 'college_suggestion':
                    prompt = reasoning.prepare_college_suggestion_prompt(
                        ctx['user_query'], ctx['suggestions']
                    )
                elif prompt_type == 'low_mark_suggestion':
                    prompt = reasoning.prepare_low_mark_suggestion_prompt(
                        ctx['mark'], ctx['percentile'], ctx['rank']
                    )
                elif prompt_type == 'management_suggestion':
                    prompt = reasoning.prepare_management_suggestion_prompt(
                        ctx['mark'], ctx['eligible_general']
                    )
                elif prompt_type == 'geo_suggestion':
                    prompt = reasoning.prepare_geo_suggestion_prompt(
                        ctx['rank'], ctx['nearby_colleges'], ctx['radius_km']
                    )
                elif prompt_type == 'choice_strategy':
                    prompt = reasoning.prepare_choice_strategy_prompt(
                        ctx['rank'], ctx['round']
                    )
                elif prompt_type == 'trend_analysis':
                    prompt = reasoning.prepare_trend_analysis_prompt()
                else:
                    print(f"SKIP (Unknown prompt_type: {prompt_type})")
                    continue
                
                # EXECUTE LLM
                response, _ = llm.generate_response(case['input'], system_prompt=prompt, stream=False)
                
                # Check constraints on RESPONSE
                errors = []
                for item in case.get('must_contain', []):
                    if item.lower() not in response.lower():
                        errors.append(f"Missing '{item}'")
                
                for item in case.get('must_not_contain', []):
                    if item.lower() in response.lower():
                        errors.append(f"Forbidden detected '{item}'")
                
                # Check max_confidence_level: fail if absolute language is used
                if case.get('max_confidence_level') == 'probabilistic':
                    absolute_phrases = ["you will get", "guaranteed", "definitely", "100%", "for sure"]
                    for phrase in absolute_phrases:
                        if phrase.lower() in response.lower():
                            errors.append(f"Absolute language detected: '{phrase}'")
                
                # Check confidence_requirements (enhanced)
                conf_req = case.get('confidence_requirements', {})
                for forbidden in conf_req.get('forbidden', []):
                    if forbidden.lower() in response.lower():
                        errors.append(f"Confidence forbidden: '{forbidden}'")
                        
                if not errors:
                    print("PASS")
                    passed += 1
                else:
                    print(f"FAIL ({', '.join(errors)})")
                    print(f"   [LLM Response]: {response[:200]}...") # Print preview
                    failed += 1
                    
        except Exception as e:
            print(f"ERROR: {e}")
            failed += 1

    print(f"\nResults: {passed} PASSED, {failed} FAILED")
    
    if failed > 0:
        return False
    return True

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
