from agent.intent_router import IntentRouter
import json

def test_ai_router():
    router = IntentRouter()
    
    test_cases = [
        {
            "name": "Greeting",
            "query": "hello there",
            "history": [],
            "expected_intent": "GREETING"
        },
        {
            "name": "Numerical Follow-up",
            "query": "173.5",
            "history": [
                {"role": "user", "content": "what colleges will I get for 173.5 cutoff in 2026"},
                {"role": "assistant", "content": "I need to know your marks first to suggest colleges based on cutoffs. What is your score?"}
            ],
            "expected_intent": "PREDICT_PERCENTILE",
            "expected_mark": 173.5
        },
        {
            "name": "Off-Topic Query",
            "query": "Who won the world cup?",
            "history": [],
            "expected_off_topic": True
        }
    ]
    
    for case in test_cases:
        print(f"\nTesting: {case['name']}")
        print(f"Query: {case['query']}")
        
        intent, entities = router.route_query(case['query'], history=case['history'])
        
        print(f"Detected Intent: {intent}")
        print(f"Entities: {entities}")
        
        if case.get("expected_off_topic"):
            assert intent == "OFF_TOPIC"
            print("✓ Correctly identified as off-topic")
        else:
            assert intent == case["expected_intent"]
            if "expected_mark" in case:
                assert entities.get("mark") == case["expected_mark"]
            print(f"✓ Correctly identified intent: {intent}")

if __name__ == "__main__":
    try:
        test_ai_router()
        print("\nAll AI Router tests passed!")
    except Exception as e:
        print(f"\nTest Failed: {e}")
