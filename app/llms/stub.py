# llm/stub.py
from typing import List, Dict, Any
from .base import LLMClient, LLMMessage

class StubLLM(LLMClient):
    def generate(self, messages: List[LLMMessage], tools=None) -> Dict[str, Any]:
        prompt = "\n".join(m["content"] for m in messages)
        
        # If this looks like a nutrition request, return valid nutrition JSON
        if "nutrition" in prompt.lower() or "meal" in prompt.lower() or "food" in prompt.lower():
            nutrition_json = """{
  "meals": [
    {
      "name": "Main Meal",
      "items": [
        {
          "name": "Ground Beef (85/15)",
          "grams": 454,
          "protein_g": 85,
          "carb_g": 0,
          "fat_g": 68,
          "kcal": 900
        },
        {
          "name": "Red Lentils (cooked)",
          "grams": 400,
          "protein_g": 32,
          "carb_g": 60,
          "fat_g": 2,
          "kcal": 380
        },
        {
          "name": "Banana",
          "grams": 120,
          "protein_g": 1.5,
          "carb_g": 31,
          "fat_g": 0.4,
          "kcal": 130
        },
        {
          "name": "Dates (4 pieces)",
          "grams": 100,
          "protein_g": 2.5,
          "carb_g": 75,
          "fat_g": 0.2,
          "kcal": 310
        },
        {
          "name": "Eggs (4 large)",
          "grams": 200,
          "protein_g": 24,
          "carb_g": 1.2,
          "fat_g": 20,
          "kcal": 280
        },
        {
          "name": "Greek Yogurt (1/2 cup)",
          "grams": 125,
          "protein_g": 15,
          "carb_g": 6,
          "fat_g": 0.5,
          "kcal": 90
        },
        {
          "name": "Whey Protein (50g)",
          "grams": 50,
          "protein_g": 40,
          "carb_g": 3,
          "fat_g": 1,
          "kcal": 180
        }
      ]
    }
  ],
  "total_protein_g": 200,
  "total_carb_g": 176.2,
  "total_fat_g": 92.1,
  "total_kcal": 2270
}"""
            return {"content": nutrition_json, "usage": {"prompt_tokens": len(prompt)//4, "completion_tokens": 200}}
        
        # Default response for non-nutrition requests
        reply = f"[stub] I read {len(prompt)} chars and would answer succinctly."
        return {"content": reply, "usage": {"prompt_tokens": len(prompt)//4, "completion_tokens": len(reply)//4}}
