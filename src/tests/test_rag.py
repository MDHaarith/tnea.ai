
import sys
import os
import logging

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ai.rag_engine import GuidelineRAG

logging.basicConfig(level=logging.INFO)

def test_rag():
    print("Initializing RAG Engine...")
    rag = GuidelineRAG()
    
    count = rag.collection.count()
    print(f"Collection count: {count}")
    
    if count == 0:
        print("ERROR: Collection is empty!")
        return
        
    queries = [
        "What is the tuition fee concession for First Graduate?",
        "Explain the procedure for special reservation for sports quota.",
        "What are the certificates needed for SC/ST students?",
        "When does the choice filling start?"
    ]
    
    print("\n--- Testing Retrieval ---")
    for q in queries:
        print(f"\nQuery: {q}")
        results = rag.query(q, n_results=1)
        if results:
            print(f"Result (First 200 chars): {results[:200]}...")
        else:
            print("Result: NO MATCH FOUND")

if __name__ == "__main__":
    test_rag()
