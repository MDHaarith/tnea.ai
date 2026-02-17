import asyncio
import os
import sys

# Add src to path
sys.path.append(os.path.join(os.getcwd(), "src"))

from agent.counsellor_agent import CounsellorAgent
from agent.session_memory import SessionMemory

async def test_agent():
    print("Initializing Agent...")
    memory = SessionMemory(session_id="test_session")
    agent = CounsellorAgent(memory=memory)
    
    query = "Hello, I have a cutoff of 195. Can I get into CEG?"
    print(f"Sending Query: {query}")
    print("--- Stream Start ---")
    
    async for chunk in agent.process_query_stream(query):
        print(chunk, end="", flush=True)
        
    print("\n--- Stream End ---")

if __name__ == "__main__":
    try:
        asyncio.run(test_agent())
    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
