from collections import deque
from typing import Dict, Deque, Tuple

# in-process STM: user_id -> deque[(role, content)]
_STORE: Dict[str, Deque[Tuple[str, str]]] = {}
MAX_TURNS = 12

def add_turn(user_id: str, role: str, content: str) -> None:
    q = _STORE.setdefault(user_id, deque(maxlen=MAX_TURNS))
    q.append((role, content))

def summary(user_id: str) -> str:
    q = _STORE.get(user_id)
    if not q: return ""
    # cheap summary: last 4 turns compressed
    last = list(q)[-4:]
    return " | ".join(f"{r}:{c[:80]}" for r,c in last)
