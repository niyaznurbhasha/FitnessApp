import uuid
from typing import Dict, List
from schemas import ChatRequest, ChatResponse, Plan, ToolCall
from prompting import build_messages
from llm.base import LLMClient
from tools.nutrition import parse_meals_freeform_llm, estimate_macros

def _detect_intent(q: str) -> str:
    ql = q.lower()
    if any(k in ql for k in ["ate", "for breakfast", "for lunch", "for dinner", "calories", "protein", "macro", "meal"]):
        return "LOG_MEAL_FREEFORM"
    if any(k in ql for k in ["injury", "hurt", "pain", "safe", "rehab"]):
        return "INJURY_GUIDE"
    if any(k in ql for k in ["usual", "leg day", "push day", "pull day", "normal workout"]):
        return "USUAL_WORKOUT_WITH_MODS"
    return "DEFAULT"

def plan(query: str) -> Plan:
    intent = _detect_intent(query)
    tools = []
    if intent == "LOG_MEAL_FREEFORM":
        tools = ["nutrition_parse", "nutrition_estimate"]
    return Plan(intent=intent, need_stm=True, need_ltm=False, tools=tools, need_retrieval=False)

def gather_context(req: ChatRequest, p: Plan, tool_payload: Dict) -> Dict:
    # STM, LTM, retrieval are stubs for now
    stm_summary = "recent conversation summary (stub)"
    tool_findings = tool_payload.get("pretty", "")
    citations = ""
    return {"stm_summary": stm_summary, "tool_findings": tool_findings, "citations": citations}

def decide_tools(p: Plan) -> List[ToolCall]:
    if "nutrition_parse" in p.tools or "nutrition_estimate" in p.tools:
        return [ToolCall(name="nutrition", args={})]
    return []

def compose_answer(llm: LLMClient, ctx: Dict, user_text: str) -> Dict:
    msgs = build_messages(user_text, ctx)
    out = llm.generate(msgs, tools=None)
    return {"text": out["content"], "usage": out.get("usage", {"prompt_tokens": 0, "completion_tokens": 0})}

class Orchestrator:
    def __init__(self, llm: LLMClient):
        self.llm = llm

    def respond(self, req: ChatRequest) -> ChatResponse:
        trace_id = str(uuid.uuid4())
        p = plan(req.text)

        # Diet tool path
        tool_payload: Dict = {}
        if p.intent == "LOG_MEAL_FREEFORM":
            items = parse_meals_freeform_llm(req.text, self.llm)
            totals = estimate_macros(items)
            pretty = (
                "Parsed meals:\n" +
                "\n".join([f"- {it['food']} {it['grams']} g ({it['prep']}): "
                           f"{it['protein']}g P, {it['carb']}g C, {it['fat']}g F, {it['kcal']} kcal"
                           for it in totals["items"]]) +
                f"\nTotals: {totals['total']['protein']}g P, {totals['total']['carb']}g C, "
                f"{totals['total']['fat']}g F, {totals['total']['kcal']} kcal"
            )
            tool_payload = {"items": items, "totals": totals, "pretty": pretty}

        tools = decide_tools(p)
        ctx = gather_context(req, p, tool_payload)
        llm_out = compose_answer(self.llm, ctx, req.text)

        return ChatResponse(
            trace_id=trace_id,
            plan=p,
            tool_calls=tools,
            answer=llm_out["text"],
            tokens_in=llm_out["usage"]["prompt_tokens"],
            tokens_out=llm_out["usage"]["completion_tokens"],
        )
