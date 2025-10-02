from fastapi.testclient import TestClient
from app.api import app

client = TestClient(app)

def test_meal_logging_path():
    r = client.post("/chat", json={"user_id":"u1","text":"Today I ate 1 lb of 90% lean ground beef, 2 cups cooked white rice, and 1 tbsp olive oil with broccoli."})
    j = r.json()
    assert j["plan"]["intent"] == "LOG_MEAL_FREEFORM"
    assert j["plan"]["tools"] == ["nutrition_parse", "nutrition_estimate"]
    assert j["tokens_in"] >= 0 and j["tokens_out"] >= 0
