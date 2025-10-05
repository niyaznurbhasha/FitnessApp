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

Step 4 – CI/CD Pipeline and React Native Frontend

Problem: Need production deployment pipeline and mobile app for iOS.

Solution: Complete CI/CD with React Native cross-platform frontend.

Key decisions:
- React Native/Expo instead of Next.js for iOS compatibility
- Same codebase for web, iOS, and Android
- GitHub Actions CI with smoke tests on every push
- Render for backend (Docker), Vercel for frontend (React Native web)
- Password protection for staging/preview deployments

Implementation approach:
- GitHub Actions: pytest + smoke tests on every push
- Docker: Production-ready container with health checks
- React Native: Cross-platform app with Expo
- Deployment: Auto-deploy on push, manual iOS builds
- Security: Environment variables, branch protection, Basic Auth

Mobile development:
- Expo Go for instant iPhone testing
- iOS Simulator for development
- EAS Build for App Store deployment
- Hot reload during development
- Native performance on mobile

Deployment pipeline:
- Backend: Render (Docker) with auto-deploy
- Frontend: Vercel (React Native web) with auto-deploy
- CI: GitHub Actions with smoke tests
- Security: Branch protection, secrets management

Step 5 – Frontend Simplification and Production Deployment

Problem: React Native/Expo had complex dependency conflicts on Vercel. Need simpler solution.

Solution: Simplified to vanilla React + Vite, easier to convert to React Native later.

Key decisions:
- Switched from Expo to Vite for web deployment
- Kept mobile-first UI design (ready for React Native conversion)
- Removed intent detection - frontend explicitly sends meal_type
- Session-based API call limiting (10 calls per browser session)

Frontend features:
- Today's Activity screen with date display
- Single Meal vs Whole Day tracking
- Final meal detection for daily totals calculation
- API call counter to manage OpenAI costs
- Password protection via environment variables

Deployment fixes:
- Removed conflicting vercel.json (use UI settings instead)
- Set Root Directory to "frontend" in Vercel
- Added CORS environment variable (FRONTEND_URL) to Render
- Fixed intent validation errors in Pydantic schemas

Step 6 – OpenAI Integration and JSON Parsing Robustness

Problem: GPT-5-mini sometimes returns incomplete or malformed JSON for complex meals.

Solution: Increased token limits and added JSON auto-repair logic.

Key fixes:
- Increased max_completion_tokens from default to 4000
- Added JSON repair logic for missing closing brackets
- Better error messages for debugging
- Handles OpenAI API quirks (max_completion_tokens vs max_tokens)

JSON auto-repair:
- Detects missing ] before totals in meals array
- Automatically fixes common malformed patterns
- Validates bracket/brace counts
- Graceful fallback to error messages if unrepairable

Production lessons:
- OpenAI models can return invalid JSON under token pressure
- Always set explicit token limits for structured outputs
- Build defensive parsing with auto-repair capabilities
- Test with complex, real-world inputs (7+ items)