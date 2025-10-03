# app/llms/stub_nutrition.py
"""
Stub LLM specifically for nutrition testing that returns predictable results.
"""

from typing import Dict, Any, List
import json


class StubNutritionLLM:
    """Stub LLM that returns predictable nutrition data for testing."""
    
    def __init__(self):
        # Pre-defined responses for different meal types
        self.responses = {
            "breakfast": {
                "meals": [
                    {
                        "name": "Breakfast",
                        "items": [
                            {
                                "name": "Eggs",
                                "grams": 100,
                                "protein_g": 12.6,
                                "carb_g": 1.1,
                                "fat_g": 9.0,
                                "kcal": 155
                            },
                            {
                                "name": "Toast",
                                "grams": 60,
                                "protein_g": 4.8,
                                "carb_g": 40.2,
                                "fat_g": 2.1,
                                "kcal": 200
                            }
                        ]
                    }
                ],
                "total_protein_g": 17.4,
                "total_carb_g": 41.3,
                "total_fat_g": 11.1,
                "total_kcal": 355
            },
            "lunch": {
                "meals": [
                    {
                        "name": "Lunch",
                        "items": [
                            {
                                "name": "Chicken Breast",
                                "grams": 150,
                                "protein_g": 35.1,
                                "carb_g": 0.0,
                                "fat_g": 3.9,
                                "kcal": 185
                            },
                            {
                                "name": "Brown Rice",
                                "grams": 100,
                                "protein_g": 2.6,
                                "carb_g": 22.0,
                                "fat_g": 0.9,
                                "kcal": 110
                            },
                            {
                                "name": "Broccoli",
                                "grams": 100,
                                "protein_g": 3.0,
                                "carb_g": 7.0,
                                "fat_g": 0.4,
                                "kcal": 34
                            }
                        ]
                    }
                ],
                "total_protein_g": 40.7,
                "total_carb_g": 29.0,
                "total_fat_g": 5.2,
                "total_kcal": 329
            },
            "dinner": {
                "meals": [
                    {
                        "name": "Dinner",
                        "items": [
                            {
                                "name": "Salmon",
                                "grams": 200,
                                "protein_g": 42.0,
                                "carb_g": 0.0,
                                "fat_g": 12.0,
                                "kcal": 280
                            },
                            {
                                "name": "Quinoa",
                                "grams": 100,
                                "protein_g": 4.4,
                                "carb_g": 22.0,
                                "fat_g": 1.9,
                                "kcal": 120
                            },
                            {
                                "name": "Mixed Vegetables",
                                "grams": 150,
                                "protein_g": 4.5,
                                "carb_g": 15.0,
                                "fat_g": 0.6,
                                "kcal": 80
                            }
                        ]
                    }
                ],
                "total_protein_g": 50.9,
                "total_carb_g": 37.0,
                "total_fat_g": 14.5,
                "total_kcal": 480
            },
            "whole_day": {
                "meals": [
                    {
                        "name": "Breakfast",
                        "items": [
                            {
                                "name": "Eggs",
                                "grams": 100,
                                "protein_g": 12.6,
                                "carb_g": 1.1,
                                "fat_g": 9.0,
                                "kcal": 155
                            },
                            {
                                "name": "Toast",
                                "grams": 60,
                                "protein_g": 4.8,
                                "carb_g": 40.2,
                                "fat_g": 2.1,
                                "kcal": 200
                            }
                        ]
                    },
                    {
                        "name": "Lunch",
                        "items": [
                            {
                                "name": "Chicken Breast",
                                "grams": 150,
                                "protein_g": 35.1,
                                "carb_g": 0.0,
                                "fat_g": 3.9,
                                "kcal": 185
                            },
                            {
                                "name": "Brown Rice",
                                "grams": 100,
                                "protein_g": 2.6,
                                "carb_g": 22.0,
                                "fat_g": 0.9,
                                "kcal": 110
                            }
                        ]
                    },
                    {
                        "name": "Dinner",
                        "items": [
                            {
                                "name": "Salmon",
                                "grams": 200,
                                "protein_g": 42.0,
                                "carb_g": 0.0,
                                "fat_g": 12.0,
                                "kcal": 280
                            },
                            {
                                "name": "Quinoa",
                                "grams": 100,
                                "protein_g": 4.4,
                                "carb_g": 22.0,
                                "fat_g": 1.9,
                                "kcal": 120
                            }
                        ]
                    }
                ],
                "total_protein_g": 101.5,
                "total_carb_g": 85.3,
                "total_fat_g": 29.8,
                "total_kcal": 1050
            }
        }
    
    def generate(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """Generate a response based on the input message."""
        if not messages:
            return {"content": "{}"}
        
        user_content = messages[0].get("content", "").lower()
        
        # Determine which response to use based on content
        if "breakfast" in user_content and "lunch" in user_content and "dinner" in user_content:
            response_data = self.responses["whole_day"]
        elif "breakfast" in user_content:
            response_data = self.responses["breakfast"]
        elif "lunch" in user_content:
            response_data = self.responses["lunch"]
        elif "dinner" in user_content:
            response_data = self.responses["dinner"]
        else:
            # Default to breakfast for single meals
            response_data = self.responses["breakfast"]
        
        # Return as JSON string
        return {
            "content": json.dumps(response_data, separators=(",", ":")),
            "usage": {"prompt_tokens": 100, "completion_tokens": 50}
        }
