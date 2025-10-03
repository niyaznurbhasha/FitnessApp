from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import date
from app.schemas import ChatRequest, ChatResponse
from app.orchestrator import Orchestrator
from app.llms.stub import StubLLM
from app.llms.openai_client import OpenAILLM
from app.models import init_db
from app.services.meal_batching import MealBatchingService
from app.schemas.nutrition import DayNutrition
import os
from dotenv import load_dotenv
load_dotenv()  # this reads .env into os.environ
app = FastAPI()
init_db()

# choose LLM: OpenAI if key present, else stub
if os.environ.get("OPENAI_API_KEY"):
    SYSTEM = "You are a nutrition calculator. Return accurate macros, micros, and kcal in JSON when asked."
    llm = OpenAILLM(model=os.environ.get("OPENAI_MODEL","gpt-4o-mini"), system_prompt=SYSTEM)
else:
    llm = StubLLM()

orc = Orchestrator(llm=llm)

# Pydantic models for meal batching API
class QuickMealRequest(BaseModel):
    user_id: str
    meal_text: str
    target_date: Optional[str] = None  # YYYY-MM-DD format

class QuickMealResponse(BaseModel):
    meal_id: int
    message: str

class DailySummaryRequest(BaseModel):
    user_id: str
    target_date: Optional[str] = None  # YYYY-MM-DD format

class DailySummaryResponse(BaseModel):
    date: str
    summary: str
    nutrition: Dict[str, Any]
    warnings: List[str]
    edit_count: int

class EditSummaryRequest(BaseModel):
    user_id: str
    target_date: str
    edited_nutrition: Dict[str, Any]

class MealHistoryResponse(BaseModel):
    history: List[Dict[str, Any]]

@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    return orc.respond(req)

# Meal batching endpoints
@app.post("/meals/quick-log", response_model=QuickMealResponse)
def log_quick_meal(req: QuickMealRequest) -> QuickMealResponse:
    """
    Log a quick meal input for later batching.
    This stores the raw text without calling the LLM.
    """
    try:
        with MealBatchingService() as service:
            meal_id = service.log_quick_meal(req.user_id, req.meal_text, req.target_date)
            return QuickMealResponse(
                meal_id=meal_id,
                message=f"Meal logged successfully. ID: {meal_id}"
            )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/meals/daily-summary", response_model=DailySummaryResponse)
def process_daily_summary(req: DailySummaryRequest) -> DailySummaryResponse:
    """
    Process all pending meals for a day into a single nutrition summary.
    This calls the LLM once per day for cost efficiency.
    """
    try:
        with MealBatchingService() as service:
            # Check if summary already exists
            existing = service.get_daily_summary(req.user_id, req.target_date)
            if existing:
                # Get edit count from database
                summary_record = service.db_session.query(service.db_session.query(service.__class__).filter_by(
                    user_id=req.user_id, 
                    date=req.target_date or date.today().isoformat()
                ).first().edit_count if hasattr(service, 'db_session') else 0)
                
                return DailySummaryResponse(
                    date=req.target_date or date.today().isoformat(),
                    summary="Summary already exists for this date",
                    nutrition=existing.model_dump(),
                    warnings=[],
                    edit_count=0  # Would need proper DB query
                )
            
            # Process pending meals
            nutrition, warnings = service.process_daily_summary(req.user_id, llm, req.target_date)
            
            return DailySummaryResponse(
                date=req.target_date or date.today().isoformat(),
                summary=f"Processed daily summary successfully",
                nutrition=nutrition.model_dump(),
                warnings=warnings,
                edit_count=0
            )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/meals/daily-summary/{user_id}", response_model=DailySummaryResponse)
def get_daily_summary(user_id: str, target_date: Optional[str] = None) -> DailySummaryResponse:
    """
    Get the processed daily summary for a user and date.
    """
    try:
        with MealBatchingService() as service:
            nutrition = service.get_daily_summary(user_id, target_date)
            if not nutrition:
                raise HTTPException(status_code=404, detail="No daily summary found for this date")
            
            return DailySummaryResponse(
                date=target_date or date.today().isoformat(),
                summary="Daily summary retrieved",
                nutrition=nutrition.model_dump(),
                warnings=[],
                edit_count=0  # Would need proper DB query
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.put("/meals/edit-summary", response_model=DailySummaryResponse)
def edit_daily_summary(req: EditSummaryRequest) -> DailySummaryResponse:
    """
    Edit an existing daily summary with post-hoc corrections.
    Limited to 1-2 edits per day to control costs.
    """
    try:
        with MealBatchingService() as service:
            # Parse the edited nutrition data
            edited_nutrition = DayNutrition.model_validate(req.edited_nutrition)
            
            # Apply the edit
            nutrition, warnings = service.edit_daily_summary(
                req.user_id, req.target_date, edited_nutrition
            )
            
            return DailySummaryResponse(
                date=req.target_date,
                summary="Daily summary updated successfully",
                nutrition=nutrition.model_dump(),
                warnings=warnings,
                edit_count=1  # Would need proper DB query
            )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/meals/history/{user_id}", response_model=MealHistoryResponse)
def get_meal_history(user_id: str, days: int = 7) -> MealHistoryResponse:
    """
    Get meal history for the past N days.
    """
    try:
        with MealBatchingService() as service:
            history = service.get_meal_history(user_id, days)
            return MealHistoryResponse(history=history)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/meals/pending/{user_id}")
def get_pending_meals(user_id: str, target_date: Optional[str] = None) -> Dict[str, Any]:
    """
    Get all pending (unprocessed) meal inputs for a user and date.
    """
    try:
        with MealBatchingService() as service:
            pending = service.get_pending_meals(user_id, target_date)
            return {
                "user_id": user_id,
                "date": target_date or date.today().isoformat(),
                "pending_count": len(pending),
                "meals": [
                    {
                        "id": meal.id,
                        "text": meal.raw_text,
                        "timestamp": meal.ts.isoformat(),
                        "edit_count": meal.edit_count
                    }
                    for meal in pending
                ]
            }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
