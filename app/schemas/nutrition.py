# app/schemas/nutrition.py
from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Dict, List, Annotated

class MealItem(BaseModel):
    name: str
    grams: float = Field(gt=0)
    protein_g: float = Field(ge=0)
    carb_g: float = Field(ge=0)
    fat_g: float = Field(ge=0)
    kcal: float = Field(ge=0)

class Meal(BaseModel):
    name: str
    items: Annotated[List[MealItem], Field(min_length=1)]

class DayNutrition(BaseModel):
    meals: Annotated[List[Meal], Field(min_length=1)]
    total_protein_g: float = Field(ge=0)
    total_carb_g: float = Field(ge=0)
    total_fat_g: float = Field(ge=0)
    total_kcal: float = Field(ge=0)

    def model_post_init(self, __context) -> None:
        """Validate that totals match sum of items."""
        total_p = sum(item.protein_g for meal in self.meals for item in meal.items)
        total_c = sum(item.carb_g for meal in self.meals for item in meal.items)
        total_f = sum(item.fat_g for meal in self.meals for item in meal.items)
        total_k = sum(item.kcal for meal in self.meals for item in meal.items)
        
        # Allow small tolerance for rounding
        if abs(self.total_protein_g - total_p) > 0.1:
            raise ValueError(f"Total protein mismatch: {self.total_protein_g} vs {total_p}")
        if abs(self.total_carb_g - total_c) > 0.1:
            raise ValueError(f"Total carb mismatch: {self.total_carb_g} vs {total_c}")
        if abs(self.total_fat_g - total_f) > 0.1:
            raise ValueError(f"Total fat mismatch: {self.total_fat_g} vs {total_f}")
        if abs(self.total_kcal - total_k) > 1:
            raise ValueError(f"Total kcal mismatch: {self.total_kcal} vs {total_k}")

def summarize_day(day: DayNutrition) -> str:
    """Human-readable summary of the day's nutrition."""
    meals = ", ".join(m.name for m in day.meals)
    return f"Meals: {meals}. Totals: {day.total_protein_g:.1f}g protein, {day.total_carb_g:.1f}g carb, {day.total_fat_g:.1f}g fat, {day.total_kcal:.0f} kcal."
