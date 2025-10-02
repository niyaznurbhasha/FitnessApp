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