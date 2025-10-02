# app/tools/nutrition.py
from __future__ import annotations
from pydantic import BaseModel, Field, conlist, ValidationError
from typing import Dict, List, Tuple, Any
import json
import math
import re

# ---------- Data models ----------

class MealItem(BaseModel):
    name: str
    grams: float = Field(gt=0)
    macros: Dict[str, float]  # protein_g, carb_g, fat_g
    micros: Dict[str, float]  # e.g., iron_mg, vit_c_mg
    kcal: float = Field(ge=0)

class Meal(BaseModel):
    name: str  # breakfast, lunch, dinner, snack, or free text
    items: conlist(MealItem, min_items=1)

class DayNutrition(BaseModel):
    meals: conlist(Meal, min_items=1)
    totals: Dict[str, float]  # sums: protein_g, carb_g, fat_g, kcal, micronutrients

# ---------- Public API ----------

def parse_day_with_llm(
    text: str,
    llm,  # any client with .generate(messages: List[dict]) -> {"content": str, "usage": {...}}
    target_schema: Dict[str, Any] | None = None,
    require_exact_totals: bool = False,
) -> Tuple[DayNutrition, List[str]]:
    """
    Convert free-text meals for a day (or a single meal) into DayNutrition via LLM JSON output.
    Returns (DayNutrition, warnings).
    Raise ValidationError if unrecoverable.
    """
    schema = target_schema or _schema_for_llm()
    messages = _build_messages(text, schema)
    out = llm.generate(messages)  # system prompt lives in the llm wrapper you set up
    raw = out.get("content", "")

    data = _safe_json_extract(raw)
    try:
        day = DayNutrition.model_validate(data)
    except ValidationError as e:
        raise ValidationError([e])  # bubble up to caller

    warnings = _validate_consistency(day, require_exact_totals=require_exact_totals)
    return day, warnings

def summarize_day(day: DayNutrition) -> str:
    """Human-readable one-liner plus totals."""
    t = day.totals
    p = round(t.get("protein_g", 0), 1)
    c = round(t.get("carb_g", 0), 1)
    f = round(t.get("fat_g", 0), 1)
    k = round(t.get("kcal", 0), 0)
    meals = ", ".join(m.name for m in day.meals)
    return f"Meals: {meals}. Totals: {p} g protein, {c} g carb, {f} g fat, {int(k)} kcal."

# ---------- Internals ----------

def _schema_for_llm() -> Dict[str, Any]:
    """
    Minimal JSON schema the LLM must follow. Keep keys stable.
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
                                    "macros": {
                                        "type": "object",
                                        "properties": {
                                            "protein_g": {"type": "number"},
                                            "carb_g": {"type": "number"},
                                            "fat_g": {"type": "number"}
                                        },
                                        "required": ["protein_g", "carb_g", "fat_g"]
                                    },
                                    "micros": {"type": "object"},  # flexible keys like iron_mg, vit_c_mg
                                    "kcal": {"type": "number"}
                                },
                                "required": ["name", "grams", "macros", "micros", "kcal"]
                            }
                        }
                    },
                    "required": ["name", "items"]
                }
            },
            "totals": {"type": "object"}  # must include sums, validated later
        },
        "required": ["meals", "totals"]
    }

def _build_messages(user_text: str, schema: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    Adds JSON-only instruction and schema. System policy stays in your LLM wrapper.
    """
    instruction = (
        "Return JSON only. No prose. "
        "Output must match the schema. "
        "All items need grams, macros in grams, micros with *_mg or *_mcg suffix, and kcal. "
        "Also include a 'totals' object with correct sums across all meals."
    )
    schema_str = json.dumps(schema, separators=(",", ":"))
    user_block = (
        f"{instruction}\n\n"
        f"Schema:\n{schema_str}\n\n"
        f"User input:\n{user_text}\n"
    )
    return [{"role": "user", "content": user_block}]

def _safe_json_extract(s: str) -> Any:
    """
    Try direct JSON parse. If that fails, extract fenced code block or best-effort braces.
    """
    s = s.strip()
    # direct
    try:
        return json.loads(s)
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
    sums: Dict[str, float] = {}
    for meal in day.meals:
        for it in meal.items:
            _acc(sums, "protein_g", it.macros.get("protein_g", 0.0))
            _acc(sums, "carb_g", it.macros.get("carb_g", 0.0))
            _acc(sums, "fat_g", it.macros.get("fat_g", 0.0))
            _acc(sums, "kcal", it.kcal)
            for k, v in it.micros.items():
                _acc(sums, k, v)

    warnings: List[str] = []
    # compare macro totals
    for key in ["protein_g", "carb_g", "fat_g", "kcal"]:
        expected = sums.get(key, 0.0)
        got = day.totals.get(key, 0.0)
        if not _close(got, expected, rel=0.05):  # 5 percent tolerance
            msg = f"totals.{key} mismatch. got={round(got,2)} expected={round(expected,2)}"
            if require_exact_totals:
                raise ValueError(msg)
            warnings.append(msg)

    # ensure micros present if any item has that micro
    for micro_key, expected in sums.items():
        if micro_key in ("protein_g", "carb_g", "fat_g", "kcal"):
            continue
        got = day.totals.get(micro_key, None)
        if got is None:
            warnings.append(f"totals missing micronutrient key: {micro_key}")
        elif not _close(got, expected, rel=0.05):
            warnings.append(f"totals.{micro_key} mismatch. got={round(got,2)} expected={round(expected,2)}")
    return warnings

def _acc(d: Dict[str, float], key: str, val: float) -> None:
    d[key] = d.get(key, 0.0) + float(val or 0.0)

def _close(a: float, b: float, rel: float = 0.05, abs_tol: float = 1e-6) -> bool:
    if a == b:
        return True
    return math.isclose(a, b, rel_tol=rel, abs_tol=abs_tol)
