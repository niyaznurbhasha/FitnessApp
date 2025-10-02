# llm/base.py
from typing import List, Optional, Dict, Any, Protocol

class LLMMessage(Dict[str, str]): ...  # {"role":"system|user|assistant","content":"..."}

class LLMClient(Protocol):
    def generate(self, messages: List[LLMMessage], tools: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        ...
