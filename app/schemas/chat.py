from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Literal

class ChatRequest(BaseModel):
    user_id: str
    text: str
    meal_type: Optional[str] = None  # "single_meal" or "whole_day"

# Intent enum as Literal for simplicity
Intent = Literal[
    "DEFAULT",
    "LOG_MEAL_FREEFORM",
    "INJURY_GUIDE",
    "USUAL_WORKOUT_WITH_MODS",
    "ASK_MEAL_INTENT",
    "LOG_SINGLE_MEAL",
    "LOG_WHOLE_DAY",
    "PROCESS_MEAL_DATA",
    "PROCESS_DAILY_SUMMARY"
]

class Plan(BaseModel):
    intent: Intent = "DEFAULT"
    need_stm: bool = True
    need_ltm: bool = False
    tools: List[str] = []
    need_retrieval: bool = False

class ToolCall(BaseModel):
    name: str
    args: Dict[str, Any]

class ChatResponse(BaseModel):
    trace_id: str
    plan: Plan
    tool_calls: List[ToolCall] = []
    answer: str
    tokens_in: int
    tokens_out: int
