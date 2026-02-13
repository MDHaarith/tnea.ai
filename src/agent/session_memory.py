import json
import os
from datetime import datetime
from typing import List, Dict, Any

class SessionMemory:
    """
    Stores session context and user preferences with persistence.
    """
    def __init__(self, session_id: str = None):
        if session_id is None:
            session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        self.session_id = session_id
        self.history: List[Dict[str, str]] = [] # Chat history
        self.user_profile: Dict[str, Any] = {
            "mark": None,
            "percentile": None,
            "rank": None,
            "preferred_location": None,
            "preferred_branch": None
        }
        self.storage_dir = os.path.join(os.getcwd(), "conversations")
        os.makedirs(self.storage_dir, exist_ok=True)
        self.file_path = os.path.join(self.storage_dir, f"{self.session_id}.json")

    def add_message(self, role: str, content: str):
        self.history.append({"role": role, "content": content})
        self.save_to_json()
        
    def update_profile(self, key: str, value: Any):
        if key in self.user_profile:
            self.user_profile[key] = value
            self.save_to_json()
            
    def get_context_string(self) -> str:
        """Returns summarized context for LLM."""
        context = "User Context:\n"
        for k, v in self.user_profile.items():
            if v:
                context += f"- {k}: {v}\n"
        return context

    def save_to_json(self):
        """Persists the session to a JSON file."""
        data = {
            "session_id": self.session_id,
            "user_profile": self.user_profile,
            "history": self.history,
            "last_updated": datetime.now().isoformat()
        }
        with open(self.file_path, "w") as f:
            json.dump(data, f, indent=4)

    def load_from_json(self):
        """Loads session data from the JSON file if it exists."""
        if os.path.exists(self.file_path):
            with open(self.file_path, "r") as f:
                data = json.load(f)
                self.user_profile = data.get("user_profile", self.user_profile)
                self.history = data.get("history", [])
                return True
        return False
