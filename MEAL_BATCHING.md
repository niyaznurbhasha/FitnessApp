# Meal Batching System

This implements the end-of-day summary approach for nutrient logging that minimizes LLM calls while providing flexibility for users.

## Key Features

### 🎯 **End-of-Day Summary (Default Flow)**
- Users log meals throughout the day as raw text
- Single LLM call processes all meals at day's end
- Cost-efficient: 1 call per day instead of 1 per meal

### ⚡ **Quick Meal Capture**
- Users can log meals mid-day without triggering LLM processing
- Raw text is stored locally for later batching
- No immediate cost - just storage

### ✏️ **Post-Hoc Edits**
- Users can make corrections after seeing LLM results
- Limited to 1-2 edits per day to control costs
- Validates consistency and provides warnings

### 📊 **Simplified Schema**
- Focus on macros + calories only (no micronutrients for now)
- Clear breakdown: totals + individual meal items
- Easy to understand and validate

## Workflow

### 1. Quick Meal Logging
```python
# User logs meals throughout the day
log_meal("Breakfast: 2 eggs, toast, coffee")
log_meal("Lunch: chicken salad with quinoa")
log_meal("Dinner: salmon with vegetables")
```

### 2. Daily Summary Processing
```python
# At end of day, process all meals with single LLM call
summary = process_daily_summary()
```

### 3. Results Display
```
📊 Daily Nutrition Summary

Totals: 120.5g protein, 180.2g carbs, 85.3g fat, 1850 kcal

Meal Breakdown:

🍽️ Breakfast: 25.2g protein, 45.1g carbs, 18.5g fat, 420 kcal
   • Eggs (100g): 12.6g protein, 1.1g carbs, 9.0g fat, 155 kcal
   • Toast (60g): 4.8g protein, 40.2g carbs, 2.1g fat, 200 kcal
   • Coffee (250ml): 0.0g protein, 0.0g carbs, 0.0g fat, 5 kcal

🍽️ Lunch: 45.8g protein, 55.3g carbs, 12.1g fat, 520 kcal
   • Chicken breast (150g): 35.1g protein, 0.0g carbs, 3.9g fat, 185 kcal
   • Quinoa (100g): 4.4g protein, 22.0g carbs, 1.9g fat, 120 kcal
   • Mixed vegetables (150g): 6.3g protein, 33.3g carbs, 6.3g fat, 215 kcal

🍽️ Dinner: 49.5g protein, 79.8g carbs, 54.7g fat, 910 kcal
   • Salmon fillet (200g): 42.0g protein, 0.0g fat, 12.0g fat, 280 kcal
   • Rice (150g): 3.0g protein, 45.0g carbs, 0.5g fat, 200 kcal
   • Vegetables (200g): 4.5g protein, 34.8g carbs, 42.2g fat, 430 kcal
```

## API Endpoints

### Quick Meal Logging
```http
POST /meals/quick-log
{
  "user_id": "user123",
  "meal_text": "Breakfast: 2 eggs, toast, coffee",
  "target_date": "2024-01-15"  // optional, defaults to today
}
```

### Daily Summary Processing
```http
POST /meals/daily-summary
{
  "user_id": "user123",
  "target_date": "2024-01-15"  // optional, defaults to today
}
```

### Get Daily Summary
```http
GET /meals/daily-summary/{user_id}?target_date=2024-01-15
```

### Edit Daily Summary
```http
PUT /meals/edit-summary
{
  "user_id": "user123",
  "target_date": "2024-01-15",
  "edited_nutrition": {
    "meals": [...],
    "total_protein_g": 125.0,
    "total_carb_g": 180.0,
    "total_fat_g": 85.0,
    "total_kcal": 1850
  }
}
```

### Get Pending Meals
```http
GET /meals/pending/{user_id}?target_date=2024-01-15
```

### Get Meal History
```http
GET /meals/history/{user_id}?days=7
```

## Chat Interface Integration

The system integrates with a button-based UI for clean user experience:

### Button-Based Workflow
```
User clicks "Nutrient Logging" button
Bot: "🍽️ I can help you with nutrition tracking! Are you:

1️⃣ **Logging a single meal**
2️⃣ **Logging your whole day's nutrition**

Please choose which one you'd like to do."

User clicks "Single Meal" button
Bot: "Got it! You're logging a single meal. Please tell me what you ate."

User: "I had breakfast: 2 eggs scrambled with 1 tbsp butter, 2 slices whole wheat toast"
Bot: "✅ Single meal logged successfully!"
```

### Log Whole Day
```
User clicks "Nutrient Logging" button
Bot: [Shows same single meal vs whole day options]

User clicks "Whole Day" button  
Bot: "Perfect! You're logging your whole day's nutrition. Please tell me everything you ate today."

User: "Today I had breakfast: 2 eggs and toast, lunch: chicken salad with quinoa, dinner: salmon with vegetables"
Bot: [Shows detailed nutrition breakdown immediately]
```

### Process Daily Summary
```
User clicks "Daily Summary" button
Bot: [Shows detailed nutrition breakdown of all pending meals]
```

## Database Schema

### RawMealInput
- Stores raw meal text before LLM processing
- Tracks processing status and edit count
- Indexed by user_id and date

### DailyNutritionSummary
- Stores processed nutrition data from LLM
- Links to raw meal inputs used
- Tracks edit count for cost control

## Cost Benefits

- **Before**: 1 LLM call per meal (e.g., 4 meals = 4 calls)
- **After**: 1 LLM call per day (e.g., 4 meals = 1 call)
- **Savings**: ~75% reduction in LLM costs for typical usage

## Setup

1. Run database migration:
```bash
python migrate_db.py
```

2. Start the server:
```bash
uvicorn app.api:app --reload
```

3. Test with example:
```bash
python example_usage.py
```

## Future Enhancements

- Add micronutrient tracking
- Implement meal templates
- Add photo recognition for meals
- Create weekly/monthly summaries
- Add nutrition goal tracking
