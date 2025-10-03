#!/usr/bin/env python3
"""
Example usage of the meal batching functionality.
This demonstrates the end-of-day summary workflow.

NOTE: This file only shows example workflows - it does NOT make actual API calls.
For testing, use the test suite in tests/test_meal_batching.py instead.
"""

def main():
    print("🍽️ Meal Batching Example - Button-Based UI Workflow")
    print("=" * 60)
    
    print("\n📱 UI-Driven User Experience:")
    print("1. User clicks 'Nutrient Logging' button")
    print("2. UI shows: 'Single Meal' or 'Whole Day' buttons")
    print("3. User clicks their choice")
    print("4. Bot processes accordingly")
    
    print("\n🔄 Example Workflow:")
    print("\n1. User clicks 'Nutrient Logging' button...")
    print("   Bot: '🍽️ I can help you with nutrition tracking! Are you:")
    print("        1️⃣ Logging a single meal")
    print("        2️⃣ Logging your whole day's nutrition")
    print("        Please choose which one you'd like to do.'")
    
    print("\n2. User clicks 'Single Meal' button...")
    print("   Bot: 'Got it! You're logging a single meal. Please tell me what you ate.'")
    print("   User: 'I had breakfast: 2 eggs scrambled with 1 tbsp butter, 2 slices whole wheat toast'")
    print("   Bot: '✅ Single meal logged successfully!'")
    
    print("\n3. Later in the day, user clicks 'Nutrient Logging' again...")
    print("   Bot: [Same flow - shows single meal vs whole day options]")
    print("   User: [Clicks 'Single Meal' again]")
    print("   Bot: 'Got it! You're logging a single meal. Please tell me what you ate.'")
    print("   User: 'I had lunch: chicken salad with quinoa'")
    print("   Bot: '✅ Single meal logged successfully!'")
    
    print("\n4. At end of day, user clicks 'Daily Summary' button...")
    print("   Bot: [Processes all pending meals with single LLM call and shows detailed breakdown]")
    
    print("\n5. Alternative: User clicks 'Whole Day' button...")
    print("   Bot: 'Perfect! You're logging your whole day's nutrition. Please tell me everything you ate today.'")
    print("   User: 'Today I had breakfast: 2 eggs and toast, lunch: chicken salad with quinoa, dinner: salmon with vegetables'")
    print("   Bot: [Processes immediately with single LLM call and shows detailed breakdown]")
    
    print("\n✅ Key Benefits:")
    print("- Clean button-based UI (no typing intent)")
    print("- Explicit user choice (single meal vs whole day)")
    print("- Only 1 LLM call per day (cost efficient)")
    print("- Users can log meals whenever convenient")
    print("- Detailed breakdown of totals and individual items")
    print("- Post-hoc editing available (1-2 edits per day)")
    print("- No confusing pending meal counts - user manages their own flow")

if __name__ == "__main__":
    main()
