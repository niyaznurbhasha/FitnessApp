# llm/stub.py
from typing import List, Dict, Any
from .base import LLMClient, LLMMessage

class StubLLM(LLMClient):
    def generate(self, messages: List[LLMMessage], tools=None) -> Dict[str, Any]:
        prompt = "\n".join(m["content"] for m in messages)
        reply = f"[stub] I read {len(prompt)} chars and would answer succinctly."
        return {"content": reply, "usage": {"prompt_tokens": len(prompt)//4, "completion_tokens": len(reply)//4}}
