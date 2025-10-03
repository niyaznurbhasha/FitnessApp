# app/services/meal_batching.py
from __future__ import annotations
from datetime import datetime, date
from typing import List, Optional, Tuple, Dict, Any
import json
from sqlalchemy.orm import Session

from ..models import RawMealInput, DailyNutritionSummary, SessionLocal
from ..schemas.nutrition import DayNutrition, summarize_day


class MealBatchingService:
    """Service for managing meal input batching and end-of-day processing."""
    
    def __init__(self, db_session: Optional[Session] = None):
        self.db_session = db_session or SessionLocal()
        self._own_session = db_session is None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._own_session:
            self.db_session.close()
    
    def log_quick_meal(self, user_id: str, meal_text: str, target_date: Optional[str] = None) -> int:
        """
        Log a quick meal input for later batching.
        
        Args:
            user_id: User identifier
            meal_text: Free-form meal description
            target_date: Date in YYYY-MM-DD format (defaults to today)
            
        Returns:
            RawMealInput ID
        """
        if target_date is None:
            target_date = date.today().isoformat()
        
        meal_input = RawMealInput(
            user_id=user_id,
            date=target_date,
            raw_text=meal_text,
            processed=False,
            edit_count=0
        )
        
        self.db_session.add(meal_input)
        self.db_session.commit()
        return meal_input.id
    
    def get_pending_meals(self, user_id: str, target_date: Optional[str] = None) -> List[RawMealInput]:
        """Get all unprocessed meal inputs for a user and date."""
        if target_date is None:
            target_date = date.today().isoformat()
        
        return self.db_session.query(RawMealInput).filter(
            RawMealInput.user_id == user_id,
            RawMealInput.date == target_date,
            RawMealInput.processed == False
        ).order_by(RawMealInput.ts).all()
    
    def process_daily_summary(self, user_id: str, llm, target_date: Optional[str] = None) -> Tuple[DayNutrition, List[str]]:
        """
        Process all pending meals for a day into a single nutrition summary.
        This is the main batching function that calls the LLM once per day.
        
        Args:
            user_id: User identifier
            llm: LLM client for nutrition parsing
            target_date: Date in YYYY-MM-DD format (defaults to today)
            
        Returns:
            Tuple of (DayNutrition, warnings)
        """
        if target_date is None:
            target_date = date.today().isoformat()
        
        # Get all pending meals for the day
        pending_meals = self.get_pending_meals(user_id, target_date)
        
        if not pending_meals:
            raise ValueError(f"No pending meals found for user {user_id} on {target_date}")
        
        # Concatenate all meal texts
        combined_text = self._combine_meal_texts(pending_meals)
        
        # Parse with LLM (single call for the entire day)
        day_nutrition, warnings = self._parse_with_llm(combined_text, llm)
        
        # Store the summary
        raw_input_ids = [str(meal.id) for meal in pending_meals]
        summary = DailyNutritionSummary(
            user_id=user_id,
            date=target_date,
            payload_json=day_nutrition.model_dump_json(),
            raw_input_ids=json.dumps(raw_input_ids),
            edit_count=0
        )
        
        self.db_session.add(summary)
        
        # Mark all meals as processed
        for meal in pending_meals:
            meal.processed = True
        
        self.db_session.commit()
        
        return day_nutrition, warnings
    
    def get_daily_summary(self, user_id: str, target_date: Optional[str] = None) -> Optional[DayNutrition]:
        """Get the processed daily summary for a user and date."""
        if target_date is None:
            target_date = date.today().isoformat()
        
        summary = self.db_session.query(DailyNutritionSummary).filter(
            DailyNutritionSummary.user_id == user_id,
            DailyNutritionSummary.date == target_date
        ).first()
        
        if summary:
            return DayNutrition.model_validate_json(summary.payload_json)
        return None
    
    def edit_daily_summary(self, user_id: str, target_date: str, edited_nutrition: DayNutrition) -> Tuple[DayNutrition, List[str]]:
        """
        Edit an existing daily summary with post-hoc corrections.
        Limited to 1-2 edits per day to control costs.
        
        Args:
            user_id: User identifier
            target_date: Date in YYYY-MM-DD format
            edited_nutrition: The corrected nutrition data
            
        Returns:
            Tuple of (validated DayNutrition, warnings)
        """
        # Get existing summary
        summary = self.db_session.query(DailyNutritionSummary).filter(
            DailyNutritionSummary.user_id == user_id,
            DailyNutritionSummary.date == target_date
        ).first()
        
        if not summary:
            raise ValueError(f"No daily summary found for user {user_id} on {target_date}")
        
        # Check edit limit (max 2 edits per day)
        if summary.edit_count >= 2:
            raise ValueError(f"Maximum edit limit (2) reached for {target_date}")
        
        # Validate the edited nutrition data
        warnings = self._validate_nutrition_data(edited_nutrition)
        
        # Update the summary
        summary.payload_json = edited_nutrition.model_dump_json()
        summary.edit_count += 1
        summary.ts = datetime.utcnow()
        
        self.db_session.commit()
        
        return edited_nutrition, warnings
    
    def get_meal_history(self, user_id: str, days: int = 7) -> List[Dict[str, Any]]:
        """Get meal history for the past N days."""
        summaries = self.db_session.query(DailyNutritionSummary).filter(
            DailyNutritionSummary.user_id == user_id
        ).order_by(DailyNutritionSummary.date.desc()).limit(days).all()
        
        history = []
        for summary in summaries:
            nutrition = DayNutrition.model_validate_json(summary.payload_json)
            history.append({
                'date': summary.date,
                'summary': summarize_day(nutrition),
                'edit_count': summary.edit_count,
                'nutrition': nutrition
            })
        
        return history
    
    def _combine_meal_texts(self, meals: List[RawMealInput]) -> str:
        """Combine multiple meal texts into a single input for LLM processing."""
        if len(meals) == 1:
            return meals[0].raw_text
        
        # For multiple meals, create a structured input
        meal_texts = []
        for i, meal in enumerate(meals, 1):
            meal_texts.append(f"Meal {i} (logged at {meal.ts.strftime('%H:%M')}): {meal.raw_text}")
        
        return f"Here are all my meals for today:\n\n" + "\n\n".join(meal_texts)
    
    def _parse_with_llm(self, text: str, llm) -> Tuple[DayNutrition, List[str]]:
        """Parse meal text with LLM using simplified schema."""
        schema = {
            "type": "object",
            "properties": {
                "meals": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "items": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "name": {"type": "string"},
                                        "grams": {"type": "number"},
                                        "protein_g": {"type": "number"},
                                        "carb_g": {"type": "number"},
                                        "fat_g": {"type": "number"},
                                        "kcal": {"type": "number"}
                                    },
                                    "required": ["name", "grams", "protein_g", "carb_g", "fat_g", "kcal"]
                                }
                            }
                        },
                        "required": ["name", "items"]
                    }
                },
                "total_protein_g": {"type": "number"},
                "total_carb_g": {"type": "number"},
                "total_fat_g": {"type": "number"},
                "total_kcal": {"type": "number"}
            },
            "required": ["meals", "total_protein_g", "total_carb_g", "total_fat_g", "total_kcal"]
        }
        
        instruction = (
            "Return JSON only. No prose. "
            "Follow the schema exactly. "
            "Calculate totals as the sum of all items across all meals. "
            "Only include protein_g, carb_g, fat_g, and kcal - no micronutrients. "
            "Be accurate with portion sizes and nutritional values."
        )
        
        schema_str = json.dumps(schema, separators=(",", ":"))
        user_block = f"{instruction}\n\nSchema:\n{schema_str}\n\nUser input:\n{text}\n"
        
        messages = [{"role": "user", "content": user_block}]
        out = llm.generate(messages)
        raw = out.get("content", "")
        
        # Parse JSON response
        data = self._safe_json_extract(raw)
        
        try:
            day = DayNutrition.model_validate(data)
        except Exception as e:
            raise ValueError(f"LLM response validation failed: {e}")
        
        warnings = self._validate_consistency(day)
        return day, warnings
    
    def _safe_json_extract(self, s: str) -> Any:
        """Extract JSON from LLM response."""
        import re
        s = s.strip()
        
        # Try direct JSON parse
        try:
            return json.loads(s)
        except Exception:
            pass
        
        # Try fenced code block
        m = re.search(r"```json\s*(\{.*?\})\s*```", s, flags=re.S | re.I)
        if m:
            try:
                return json.loads(m.group(1))
            except Exception:
                pass
        
        # Try first and last brace
        i, j = s.find("{"), s.rfind("}")
        if i != -1 and j != -1 and j > i:
            chunk = s[i : j + 1]
            return json.loads(chunk)
        
        raise ValueError("LLM did not return valid JSON")
    
    def _validate_consistency(self, day: DayNutrition) -> List[str]:
        """Check that totals match sum of items."""
        warnings = []
        
        # Calculate expected totals
        expected_protein = sum(item.protein_g for meal in day.meals for item in meal.items)
        expected_carb = sum(item.carb_g for meal in day.meals for item in meal.items)
        expected_fat = sum(item.fat_g for meal in day.meals for item in meal.items)
        expected_kcal = sum(item.kcal for meal in day.meals for item in meal.items)
        
        # Check with tolerance
        if abs(day.total_protein_g - expected_protein) > 0.1:
            warnings.append(f"Protein total mismatch: {day.total_protein_g:.1f} vs {expected_protein:.1f}")
        
        if abs(day.total_carb_g - expected_carb) > 0.1:
            warnings.append(f"Carb total mismatch: {day.total_carb_g:.1f} vs {expected_carb:.1f}")
        
        if abs(day.total_fat_g - expected_fat) > 0.1:
            warnings.append(f"Fat total mismatch: {day.total_fat_g:.1f} vs {expected_fat:.1f}")
        
        if abs(day.total_kcal - expected_kcal) > 1:
            warnings.append(f"Calorie total mismatch: {day.total_kcal:.0f} vs {expected_kcal:.0f}")
        
        return warnings
    
    def _validate_nutrition_data(self, nutrition: DayNutrition) -> List[str]:
        """Validate nutrition data for reasonable values."""
        warnings = []
        
        if nutrition.total_kcal < 0:
            warnings.append("Negative calories detected")
        
        if nutrition.total_kcal > 10000:
            warnings.append("Unusually high calorie count")
        
        if nutrition.total_protein_g < 0:
            warnings.append("Negative protein detected")
        
        if nutrition.total_carb_g < 0:
            warnings.append("Negative carbs detected")
        
        if nutrition.total_fat_g < 0:
            warnings.append("Negative fat detected")
        
        return warnings


# Convenience functions
def log_quick_meal(user_id: str, meal_text: str, target_date: Optional[str] = None) -> int:
    """Quick function to log a meal input."""
    with MealBatchingService() as service:
        return service.log_quick_meal(user_id, meal_text, target_date)


def process_daily_summary(user_id: str, llm, target_date: Optional[str] = None) -> Tuple[DayNutrition, List[str]]:
    """Quick function to process daily summary."""
    with MealBatchingService() as service:
        return service.process_daily_summary(user_id, llm, target_date)


def get_daily_summary(user_id: str, target_date: Optional[str] = None) -> Optional[DayNutrition]:
    """Quick function to get daily summary."""
    with MealBatchingService() as service:
        return service.get_daily_summary(user_id, target_date)
