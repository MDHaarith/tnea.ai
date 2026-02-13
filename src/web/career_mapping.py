from llm_gateway import LLMClient
from ai.prompts import CAREER_MAPPING_PROMPT

class CareerMapper:
    def __init__(self):
        self.llm = LLMClient()

    def map_career(self, branch: str) -> str:
        """
        Maps engineering branch to career paths using LLM.
        """
        prompt = f"Engineering Branch: {branch}\n\nMap this branch to potential career paths and higher studies."
        response, _ = self.llm.generate_response(prompt, system_prompt=CAREER_MAPPING_PROMPT)
        return response
