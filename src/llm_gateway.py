import logging
from openai import OpenAI
import json
import time
from config import config

logger = logging.getLogger("tnea_ai.llm")


class LLMClient:
    def __init__(self, model_name=None, base_url=None, api_key=None):
        self.model_name = model_name or config.MODEL_NAME
        self.base_url = base_url or config.NVIDIA_API_BASE
        self.api_key = api_key or config.NVIDIA_API_KEY
        
        if not self.api_key:
             raise ValueError("API Key is required. Set NVIDIA_API_KEY in .env or pass it explicitly.")

        self.client = OpenAI(
            base_url=self.base_url,
            api_key=self.api_key
        )
        logger.info(f"LLM client initialized: model={self.model_name}")

    def generate_response(self, prompt: str, system_prompt: str = None, context: list = None, stream: bool = False):
        """Generates a response from the LLM using NVIDIA API."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        if context:
            messages.extend(context)
            
        messages.append({"role": "user", "content": prompt})

        try:
            if stream:
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    temperature=0.6,
                    top_p=0.7,
                    max_tokens=2048,
                    stream=True
                )
                def streamer():
                    full_response = ""
                    for chunk in response:
                        if chunk.choices and chunk.choices[0].delta.content is not None:
                            token = chunk.choices[0].delta.content
                            full_response += token
                            yield token, []
                    yield "", []
                return streamer()
            else:
                completion = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    temperature=0.6,
                    top_p=0.7,
                    max_tokens=2048,
                    stream=False
                )
                content = completion.choices[0].message.content
                return content, []
        except Exception as e:
            error_msg = f"Error communicating with NVIDIA API: {str(e)}"
            logger.error(error_msg)
            if stream:
                def error_streamer():
                    yield f"⚠️ AI Service Unavailable: {error_msg}", []
                return error_streamer()
            return error_msg, []

    def chat(self, messages: list) -> str:
        """Chat with the LLM using the completions API."""
        try:
            completion = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.6,
                top_p=0.7,
                max_tokens=2048,
                stream=False
            )
            return completion.choices[0].message.content
        except Exception as e:
            logger.error(f"Error communicating with NVIDIA API: {str(e)}")
            return f"Error communicating with NVIDIA API: {str(e)}"

if __name__ == "__main__":
    try:
        logger.info(f"Loading config... Model: {config.MODEL_NAME}")
        client = LLMClient()
        logger.info(f"Testing connection to NVIDIA API...")
        response, _ = client.generate_response("Hello, are you online?", system_prompt="You are a helpful AI assistant.")
        logger.info(f"Response: {response}")
    except Exception as e:
        logger.error(f"FAILED: {e}")
