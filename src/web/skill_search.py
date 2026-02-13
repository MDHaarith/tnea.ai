from llm_gateway import LLMClient
from ai.prompts import SKILL_SEARCH_PROMPT

class SkillSearch:
    def __init__(self):
        self.llm = LLMClient()

    def search_skills(self, branch: str) -> str:
        """
        Simulates a web search for skills using the LLM's knowledge tailored by the prompt.
        """
        prompt = f"Branch: {branch}\n\nSearch for relevant skills and industry trends."
        response, _ = self.llm.generate_response(prompt, system_prompt=SKILL_SEARCH_PROMPT)
        return response
