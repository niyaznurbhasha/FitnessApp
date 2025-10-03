# app/orchestrator.py
import uuid, json
from typing import Dict, List
from app.schemas import ChatRequest, ChatResponse, Plan, ToolCall
from app.prompting import build_messages
from app.llms.base import LLMClient
from app.llms.tools.nutrition import parse_day_with_llm, summarize_day
from app.memory import stm
from app.models import SessionLocal, DayNutritionArtifact, Message
from app.services.meal_batching import MealBatchingService
from app.utils.io import write_json_atomic
from pathlib import Path

# ---------- intent + plan ----------

def _detect_intent(q: str) -> str:
    ql = q.lower()
    # Only detect clear daily summary requests
    summary_keywords = [
        "daily summary", "end of day", "process meals", "summarize today",
        "today's nutrition", "daily totals", "process all meals"
    ]
    
    if any(k in ql for k in summary_keywords):
        return "PROCESS_DAILY_SUMMARY"
    
    # Check for user responses to meal intent question
    single_meal_responses = [
        "1", "single meal", "one meal", "just one meal", "single", "one",
        "logging a single meal", "i'm logging a single meal"
    ]
    
    whole_day_responses = [
        "2", "whole day", "entire day", "all meals", "whole day's nutrition",
        "logging my whole day", "i'm logging my whole day", "all my meals today"
    ]
    
    if any(k in ql for k in single_meal_responses):
        return "LOG_SINGLE_MEAL"
    elif any(k in ql for k in whole_day_responses):
        return "LOG_WHOLE_DAY"
    else:
        # Check if this looks like actual meal data (after user has been asked for intent)
        meal_data_indicators = [
            "i had", "i ate", "breakfast:", "lunch:", "dinner:", "snack:",
            "today i had", "for breakfast", "for lunch", "for dinner"
        ]
        
        if any(k in ql for k in meal_data_indicators):
            return "PROCESS_MEAL_DATA"
        
        # For any other nutrition-related input, ask for clarification
        nutrition_keywords = [
            "breakfast", "lunch", "dinner", "snack",
            "ate", "i ate", "what i ate",
            "macros", "micros", "calories", "kcal", "protein", "carbs", "fat",
            "meal", "food", "nutrition"
        ]
        
        if any(k in ql for k in nutrition_keywords):
            return "ASK_MEAL_INTENT"
        else:
            return "DEFAULT"

def plan(query: str) -> Plan:
    intent = _detect_intent(query)
    tools = []
    if intent == "PROCESS_DAILY_SUMMARY":
        tools = ["daily_summary"]
    elif intent == "PROCESS_MEAL_DATA":
        tools = ["meal_batching"]
    # No tools for ASK_MEAL_INTENT, LOG_SINGLE_MEAL, LOG_WHOLE_DAY - we'll handle them in the orchestrator
    return Plan(intent=intent, need_stm=True, need_ltm=False, tools=tools, need_retrieval=False)

# ---------- context ----------

def _gather_context(user_id: str, tool_payload: Dict) -> Dict:
    return {
        "stm_summary": stm.summary(user_id),
        "tool_findings": tool_payload.get("pretty", ""),
        "citations": ""
    }

# ---------- orchestrator ----------

class Orchestrator:
    def __init__(self, llm: LLMClient):
        self.llm = llm

    def respond(self, req: ChatRequest) -> ChatResponse:
        trace_id = str(uuid.uuid4())
        p = plan(req.text)

        # log user turn (STM + DB)
        stm.add_turn(req.user_id, "user", req.text)
        with SessionLocal() as s:
            s.add(Message(user_id=req.user_id, role="user", content=req.text))
            s.commit()

        tool_payload: Dict = {}

        # -------- Ask for meal intent --------
        if p.intent == "ASK_MEAL_INTENT":
            out_content = "🍽️ I can help you with nutrition tracking! Are you:\n\n"
            out_content += "1️⃣ **Logging a single meal**\n"
            out_content += "2️⃣ **Logging your whole day's nutrition**\n\n"
            out_content += "Please choose which one you'd like to do."

            # log assistant turn
            stm.add_turn(req.user_id, "assistant", out_content)
            with SessionLocal() as s:
                s.add(Message(user_id=req.user_id, role="assistant", content=out_content))
                s.commit()

            return ChatResponse(
                trace_id=trace_id,
                plan=p,
                tool_calls=[],
                answer=out_content,
                tokens_in=0,
                tokens_out=0,
            )

        # -------- Log single meal --------
        elif p.intent == "LOG_SINGLE_MEAL":
            out_content = "Got it! You're logging a single meal. Please tell me what you ate."

            # log assistant turn
            stm.add_turn(req.user_id, "assistant", out_content)
            with SessionLocal() as s:
                s.add(Message(user_id=req.user_id, role="assistant", content=out_content))
                s.commit()

            return ChatResponse(
                trace_id=trace_id,
                plan=p,
                tool_calls=[],
                answer=out_content,
                tokens_in=0,
                tokens_out=0,
            )

        # -------- Log whole day --------
        elif p.intent == "LOG_WHOLE_DAY":
            out_content = "Perfect! You're logging your whole day's nutrition. Please tell me everything you ate today."

            # log assistant turn
            stm.add_turn(req.user_id, "assistant", out_content)
            with SessionLocal() as s:
                s.add(Message(user_id=req.user_id, role="assistant", content=out_content))
                s.commit()

            return ChatResponse(
                trace_id=trace_id,
                plan=p,
                tool_calls=[],
                answer=out_content,
                tokens_in=0,
                tokens_out=0,
            )

        # -------- Process meal data --------
        elif p.intent == "PROCESS_MEAL_DATA":
            # Check if this looks like a single meal or whole day
            ql = req.text.lower()
            whole_day_indicators = [
                "today i had", "breakfast:", "lunch:", "dinner:", "snack:",
                "for breakfast", "for lunch", "for dinner", "and then", "also had"
            ]
            
            is_whole_day = any(indicator in ql for indicator in whole_day_indicators)
            
            if is_whole_day:
                # Process as whole day (single LLM call)
                try:
                    day_nutrition, warnings = parse_day_with_llm(req.text, self.llm)
                    
                    # Create detailed summary
                    out_content = f"📊 **Daily Nutrition Summary**\n\n"
                    out_content += f"**Totals:** {day_nutrition.total_protein_g:.1f}g protein, {day_nutrition.total_carb_g:.1f}g carbs, {day_nutrition.total_fat_g:.1f}g fat, {day_nutrition.total_kcal:.0f} kcal\n\n"
                    
                    out_content += "**Meal Breakdown:**\n"
                    for meal in day_nutrition.meals:
                        meal_protein = sum(item.protein_g for item in meal.items)
                        meal_carb = sum(item.carb_g for item in meal.items)
                        meal_fat = sum(item.fat_g for item in meal.items)
                        meal_kcal = sum(item.kcal for item in meal.items)
                        
                        out_content += f"\n🍽️ **{meal.name}:** {meal_protein:.1f}g protein, {meal_carb:.1f}g carbs, {meal_fat:.1f}g fat, {meal_kcal:.0f} kcal\n"
                        
                        for item in meal.items:
                            out_content += f"   • {item.name} ({item.grams:.0f}g): {item.protein_g:.1f}g protein, {item.carb_g:.1f}g carbs, {item.fat_g:.1f}g fat, {item.kcal:.0f} kcal\n"
                    
                    if warnings:
                        out_content += f"\n⚠️ **Warnings:** {', '.join(warnings)}"
                    
                    # Store in database
                    with SessionLocal() as s:
                        s.add(DayNutritionArtifact(user_id=req.user_id, payload_json=json.dumps(day_nutrition.model_dump())))
                        s.commit()
                    
                except Exception as e:
                    out_content = f"Error processing your nutrition data: {str(e)}"
            else:
                # Process as single meal (store for batching)
                with MealBatchingService() as service:
                    meal_id = service.log_quick_meal(req.user_id, req.text)
                    
                    out_content = f"✅ Single meal logged successfully!"

            # log assistant turn
            stm.add_turn(req.user_id, "assistant", out_content)
            with SessionLocal() as s:
                s.add(Message(user_id=req.user_id, role="assistant", content=out_content))
                s.commit()

            return ChatResponse(
                trace_id=trace_id,
                plan=p,
                tool_calls=[ToolCall(name="meal_batching", args={})],
                answer=out_content,
                tokens_in=0,
                tokens_out=0,
            )

        # -------- Daily summary tool branch --------
        elif p.intent == "PROCESS_DAILY_SUMMARY":
            with MealBatchingService() as service:
                # Check if there are pending meals
                pending = service.get_pending_meals(req.user_id)
                if not pending:
                    out_content = "No pending meals found for today. Log some meals first!"
                else:
                    # Process all pending meals into daily summary (single LLM call)
                    try:
                        day_nutrition, warnings = service.process_daily_summary(req.user_id, self.llm)
                        
                        # Create detailed summary showing totals and individual meal breakdown
                        out_content = f"📊 **Daily Nutrition Summary**\n\n"
                        out_content += f"**Totals:** {day_nutrition.total_protein_g:.1f}g protein, {day_nutrition.total_carb_g:.1f}g carbs, {day_nutrition.total_fat_g:.1f}g fat, {day_nutrition.total_kcal:.0f} kcal\n\n"
                        
                        out_content += "**Meal Breakdown:**\n"
                        for meal in day_nutrition.meals:
                            meal_protein = sum(item.protein_g for item in meal.items)
                            meal_carb = sum(item.carb_g for item in meal.items)
                            meal_fat = sum(item.fat_g for item in meal.items)
                            meal_kcal = sum(item.kcal for item in meal.items)
                            
                            out_content += f"\n🍽️ **{meal.name}:** {meal_protein:.1f}g protein, {meal_carb:.1f}g carbs, {meal_fat:.1f}g fat, {meal_kcal:.0f} kcal\n"
                            
                            for item in meal.items:
                                out_content += f"   • {item.name} ({item.grams:.0f}g): {item.protein_g:.1f}g protein, {item.carb_g:.1f}g carbs, {item.fat_g:.1f}g fat, {item.kcal:.0f} kcal\n"
                        
                        if warnings:
                            out_content += f"\n⚠️ **Warnings:** {', '.join(warnings)}"
                        
                        tool_payload["pretty"] = out_content
                        
                    except Exception as e:
                        out_content = f"Error processing daily summary: {str(e)}"

            # log assistant turn
            stm.add_turn(req.user_id, "assistant", out_content)
            with SessionLocal() as s:
                s.add(Message(user_id=req.user_id, role="assistant", content=out_content))
                s.commit()

            return ChatResponse(
                trace_id=trace_id,
                plan=p,
                tool_calls=[ToolCall(name="daily_summary", args={})],
                answer=out_content,
                tokens_in=0,
                tokens_out=0,
            )

        # -------- Default LLM branch --------
        ctx = _gather_context(req.user_id, tool_payload)
        msgs = build_messages(req.text, ctx)
        out = self.llm.generate(msgs, tools=None)

        # log assistant turn
        stm.add_turn(req.user_id, "assistant", out["content"])
        with SessionLocal() as s:
            s.add(Message(user_id=req.user_id, role="assistant", content=out["content"]))
            s.commit()

        return ChatResponse(
            trace_id=trace_id,
            plan=p,
            tool_calls=[],
            answer=out["content"],
            tokens_in=out["usage"]["prompt_tokens"],
            tokens_out=out["usage"]["completion_tokens"],
        )
