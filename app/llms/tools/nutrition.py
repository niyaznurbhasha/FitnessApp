# app/tools/nutrition.py
from __future__ import annotations
from pydantic import BaseModel, Field, ValidationError
from typing import Dict, List, Tuple, Any
from typing_extensions import Annotated
import json
import math
import re

# Import the simplified schema
from ...schemas.nutrition import DayNutrition, Meal, MealItem, summarize_day


# ---------- Public API ----------

from pydantic import ValidationError

def parse_day_with_llm(
    text: str,
    llm,
    target_schema: Dict[str, Any] | None = None,
    require_exact_totals: bool = False,
) -> Tuple[DayNutrition, List[str]]:
    schema = target_schema or _schema_for_llm()
    messages = _build_messages(text, schema)
    out = llm.generate(messages)
    raw = out.get("content", "")
    
    try:
        data = _safe_json_extract(raw)
    except Exception as e:
        raise ValueError(f"Failed to parse LLM JSON response. Error: {str(e)}")

    try:
        day = DayNutrition.model_validate(data)
    except ValidationError as e:
        raise e

    warnings = _validate_consistency(day, require_exact_totals=require_exact_totals)
    return day, warnings

# ---------- Internals ----------

def _schema_for_llm() -> Dict[str, Any]:
    """
    Simplified JSON schema for macros and calories only.
    """
    return {
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

def _build_messages(user_text: str, schema: Dict[str, Any]) -> List[Dict[str, str]]:
    instruction = (
        "Return JSON only. No prose. "
        "Follow the schema exactly. "
        "Calculate totals as the sum of all items across all meals. "
        "Only include protein_g, carb_g, fat_g, and kcal - no micronutrients. "
        "Be accurate with portion sizes and nutritional values."
    )
    schema_str = json.dumps(schema, separators=(",", ":"))
    user_block = f"{instruction}\n\nSchema:\n{schema_str}\n\nUser input:\n{user_text}\n"
    return [{"role": "user", "content": user_block}]


def _safe_json_extract(s: str) -> Any:
    """
    Try direct JSON parse. If that fails, extract fenced code block or best-effort braces.
    Also tries to fix common JSON errors like missing closing brackets.
    """
    s = s.strip()
    # direct
    try:
        return json.loads(s)
    except Exception:
        pass
    
    # Try to fix missing closing bracket for meals array
    # Pattern: },"total_protein_g": should be }],"total_protein_g":
    if '}",' in s and '"total_protein_g"' in s:
        # Find the position right before "total_protein_g"
        idx = s.find('"total_protein_g"')
        if idx > 0:
            # Check if there's a missing ] before the totals
            before_totals = s[:idx]
            if before_totals.count('[') > before_totals.count(']'):
                # Add missing ]
                fixed = s[:idx] + '],' + s[idx:]
                fixed = fixed.replace('},],"total', '}],"total')  # Fix double comma
                try:
                    return json.loads(fixed)
                except Exception:
                    pass
    
    # fenced ```json ... ```
    m = re.search(r"```json\s*(\{.*?\})\s*```", s, flags=re.S | re.I)
    if m:
        try:
            return json.loads(m.group(1))
        except Exception:
            pass
    # first and last brace
    i, j = s.find("{"), s.rfind("}")
    if i != -1 and j != -1 and j > i:
        chunk = s[i : j + 1]
        return json.loads(chunk)
    raise ValueError("LLM did not return valid JSON")

def _validate_consistency(day: DayNutrition, require_exact_totals: bool) -> List[str]:
    """
    Check that totals match sum of items. Returns warnings. Optionally enforce exact match.
    """
    # Calculate expected totals
    expected_protein = sum(item.protein_g for meal in day.meals for item in meal.items)
    expected_carb = sum(item.carb_g for meal in day.meals for item in meal.items)
    expected_fat = sum(item.fat_g for meal in day.meals for item in meal.items)
    expected_kcal = sum(item.kcal for meal in day.meals for item in meal.items)

    warnings: List[str] = []
    
    # Check with tolerance
    if not _close(day.total_protein_g, expected_protein, rel=0.05):
        msg = f"Protein total mismatch: {day.total_protein_g:.1f} vs {expected_protein:.1f}"
        if require_exact_totals:
            raise ValueError(msg)
        warnings.append(msg)
    
    if not _close(day.total_carb_g, expected_carb, rel=0.05):
        msg = f"Carb total mismatch: {day.total_carb_g:.1f} vs {expected_carb:.1f}"
        if require_exact_totals:
            raise ValueError(msg)
        warnings.append(msg)
    
    if not _close(day.total_fat_g, expected_fat, rel=0.05):
        msg = f"Fat total mismatch: {day.total_fat_g:.1f} vs {expected_fat:.1f}"
        if require_exact_totals:
            raise ValueError(msg)
        warnings.append(msg)
    
    if not _close(day.total_kcal, expected_kcal, rel=0.05):
        msg = f"Calorie total mismatch: {day.total_kcal:.0f} vs {expected_kcal:.0f}"
        if require_exact_totals:
            raise ValueError(msg)
        warnings.append(msg)
    
    return warnings

def _close(a: float, b: float, rel: float = 0.05, abs_tol: float = 1e-6) -> bool:
    if a == b:
        return True
    return math.isclose(a, b, rel_tol=rel, abs_tol=abs_tol)
