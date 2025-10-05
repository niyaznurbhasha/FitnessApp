from typing import List, Dict, Any
import os
from openai import OpenAI

class OpenAILLM:
    def __init__(self, model: str = "gpt-5-mini", system_prompt: str = ""):
        # New project-based auth requires both API key and project ID
        self.client = OpenAI(
            api_key=os.environ["OPENAI_API_KEY"],
            project=os.environ.get("OPENAI_PROJECT_ID")  # <-- add this
        )
        self.model = model
        self.system_prompt = system_prompt

    def generate(self, messages: List[Dict[str, str]], tools: Any = None) -> Dict[str, Any]:
        msgs = []
        if self.system_prompt:
            msgs.append({"role": "system", "content": self.system_prompt})
        msgs += messages
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=msgs,
            max_completion_tokens=4000,  # Higher limit for complex nutrition responses with many items
        )
        choice = resp.choices[0].message
        content = choice.content or ""
        usage = resp.usage or None
        return {
            "content": content,
            "usage": {
                "prompt_tokens": getattr(usage, "prompt_tokens", 0),
                "completion_tokens": getattr(usage, "completion_tokens", 0)
            }
        }
