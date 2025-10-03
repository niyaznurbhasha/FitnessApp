# app/services/meal_batching_memory.py
"""
In-memory version of meal batching service for testing.
Uses dicts instead of database: day_inputs[(user,date)] -> [texts], day_results[(user,date)] -> DayNutrition
"""

from __future__ import annotations
from datetime import date
from typing import List, Optional, Tuple, Dict, Any
from collections import defaultdict
import json
import re
import math

from ..schemas.nutrition import DayNutrition, summarize_day


class InMemoryMealBatchingService:
    """In-memory meal batching service for testing."""
    
    def __init__(self):
        # day_inputs[(user_id, date)] -> List[str] (raw meal texts)
        self.day_inputs: Dict[Tuple[str, str], List[str]] = defaultdict(list)
        
        # day_results[(user_id, date)] -> DayNutrition (processed results)
        self.day_results: Dict[Tuple[str, str], DayNutrition] = {}
        
        # edit_counts[(user_id, date)] -> int (track edits per day)
        self.edit_counts: Dict[Tuple[str, str], int] = defaultdict(int)
    
    def log_quick_meal(self, user_id: str, meal_text: str, target_date: Optional[str] = None) -> int:
        """
        Log a quick meal input for later batching.
        
        Args:
            user_id: User identifier
            meal_text: Free-form meal description
            target_date: Date in YYYY-MM-DD format (defaults to today)
            
        Returns:
            Meal ID (just index in the list)
        """
        if target_date is None:
            target_date = date.today().isoformat()
        
        key = (user_id, target_date)
        self.day_inputs[key].append(meal_text)
        
        # Return the index as the "meal_id"
        return len(self.day_inputs[key]) - 1
    
    def get_pending_meals(self, user_id: str, target_date: Optional[str] = None) -> List[str]:
        """Get all unprocessed meal inputs for a user and date."""
        if target_date is None:
            target_date = date.today().isoformat()
        
        key = (user_id, target_date)
        return self.day_inputs[key].copy()
    
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
        
        key = (user_id, target_date)
        pending_meals = self.day_inputs[key]
        
        if not pending_meals:
            raise ValueError(f"No pending meals found for user {user_id} on {target_date}")
        
        # Concatenate all meal texts
        combined_text = self._combine_meal_texts(pending_meals)
        
        # Parse with LLM (single call for the entire day)
        day_nutrition, warnings = self._parse_with_llm(combined_text, llm)
        
        # Store the result
        self.day_results[key] = day_nutrition
        
        # Clear pending meals (they're now processed)
        self.day_inputs[key] = []
        
        return day_nutrition, warnings
    
    def get_daily_summary(self, user_id: str, target_date: Optional[str] = None) -> Optional[DayNutrition]:
        """Get the processed daily summary for a user and date."""
        if target_date is None:
            target_date = date.today().isoformat()
        
        key = (user_id, target_date)
        return self.day_results.get(key)
    
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
        key = (user_id, target_date)
        
        if key not in self.day_results:
            raise ValueError(f"No daily summary found for user {user_id} on {target_date}")
        
        # Check edit limit (max 2 edits per day)
        if self.edit_counts[key] >= 2:
            raise ValueError(f"Maximum edit limit (2) reached for {target_date}")
        
        # Validate the edited nutrition data
        warnings = self._validate_nutrition_data(edited_nutrition)
        
        # Update the summary
        self.day_results[key] = edited_nutrition
        self.edit_counts[key] += 1
        
        return edited_nutrition, warnings
    
    def get_meal_history(self, user_id: str, days: int = 7) -> List[Dict[str, Any]]:
        """Get meal history for the past N days."""
        # For simplicity, just return all results for the user
        history = []
        for (uid, date_str), nutrition in self.day_results.items():
            if uid == user_id:
                history.append({
                    'date': date_str,
                    'summary': summarize_day(nutrition),
                    'edit_count': self.edit_counts.get((uid, date_str), 0),
                    'nutrition': nutrition
                })
        
        # Sort by date descending
        history.sort(key=lambda x: x['date'], reverse=True)
        return history[:days]
    
    def _combine_meal_texts(self, meals: List[str]) -> str:
        """Combine multiple meal texts into a single input for LLM processing."""
        if len(meals) == 1:
            return meals[0]
        
        # For multiple meals, create a structured input
        meal_texts = []
        for i, meal in enumerate(meals, 1):
            meal_texts.append(f"Meal {i}: {meal}")
        
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
        if not self._close(day.total_protein_g, expected_protein, rel=0.05):
            warnings.append(f"Protein total mismatch: {day.total_protein_g:.1f} vs {expected_protein:.1f}")
        
        if not self._close(day.total_carb_g, expected_carb, rel=0.05):
            warnings.append(f"Carb total mismatch: {day.total_carb_g:.1f} vs {expected_carb:.1f}")
        
        if not self._close(day.total_fat_g, expected_fat, rel=0.05):
            warnings.append(f"Fat total mismatch: {day.total_fat_g:.1f} vs {expected_fat:.1f}")
        
        if not self._close(day.total_kcal, expected_kcal, rel=0.05):
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
    
    def _close(self, a: float, b: float, rel: float = 0.05, abs_tol: float = 1e-6) -> bool:
        """Check if two numbers are close within tolerance."""
        if a == b:
            return True
        return math.isclose(a, b, rel_tol=rel, abs_tol=abs_tol)
    
    def clear_all(self):
        """Clear all data for testing."""
        self.day_inputs.clear()
        self.day_results.clear()
        self.edit_counts.clear()
