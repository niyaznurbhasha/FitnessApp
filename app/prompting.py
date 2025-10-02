# prompting.py
from typing import Dict

SYSTEM = "You are a concise fitness coach. Prioritize user data when available. Cite sources only if provided."

def build_messages(user_text: str, ctx: Dict) -> list:
    stm = ctx.get("stm_summary", "")
    tool_findings = ctx.get("tool_findings", "")
    citations = ctx.get("citations", "")
    user_block = f"Context:\nShort-term: {stm}\nFindings: {tool_findings}\nCitations: {citations}\nUser: {user_text}"
    return [{"role":"system","content":SYSTEM},
            {"role":"user","content":user_block}]
