Initial scope

Goal: Build a fitness chatbot with RAG + memory + tools.

Planned features: track workouts, diet, injuries; provide personalized, explainable recommendations; multi-turn conversation with state.

Tech: FastAPI backend, SQLite → Postgres, Redis for STM, Celery for async, vector DB later.

Step 1 – Core loop (MVP agent skeleton)

Defined strict Pydantic schemas for ChatRequest, ChatResponse, Plan.

Added orchestrator with planner (intent detection), context gathering, tool execution, and answer composition.

Wrapped LLM behind a provider-agnostic interface (LLMClient) using Protocol.

Added stub LLM to simulate outputs for development and testing.

Built a simple prompt composer with context slots (STM, tool findings, citations).

Step 2 – First tool focus: nutrition

Instead of implementing all tools at once, decided to prioritize diet logging.

Original design: regex parsing + macro tables.

Revised decision: drop heuristics/presets → use LLM directly for parsing.

Defined schema DayNutrition → meals, items (name, grams, macros, micros, kcal), totals.

Plan: LLM takes free-text daily/meal description, outputs JSON in schema, validated in code.

Validation checks: totals vs item sums, micronutrient presence, clarifying Qs if inconsistent.

Step 3 – Meal batching system (cost optimization)

Problem: LLM calls per meal are expensive. Need to minimize calls while maintaining user experience.

Solution: End-of-day summary approach with batching.

Key decisions:
- Store raw meal inputs locally/cheap DB before LLM processing
- Batch all meals for a day into single LLM call at day's end
- Allow 1-2 post-hoc edits per day to fix mistakes
- Remove micronutrients for now, focus on macros + calories only

Implementation approach:
- In-memory storage for testing: day_inputs[(user,date)] → [texts], day_results[(user,date)] → DayNutrition
- Swap to SQLite/Postgres after tests pass
- Keep function signatures consistent

User experience:
- Button-based UI: "Nutrient Logging" → "Single Meal" or "Whole Day"
- Explicit user intent (no keyword guessing)
- Clean responses without confusing pending counts
- User manages their own flow

Schema simplification:
- Removed micronutrients, kept only protein_g, carb_g, fat_g, kcal
- Built-in validation: totals must match sum of items
- Clear breakdown: totals + individual meal items

Testing strategy:
- Comprehensive test suite with in-memory storage
- Golden test: 3 meals → finalize → check totals within tolerance
- Edit flow test: post-hoc edit → re-finalize overwrites
- All core functionality verified before database migration