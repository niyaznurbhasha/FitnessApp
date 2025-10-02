# api.py
from fastapi import FastAPI
from schemas import ChatRequest, ChatResponse
from orchestrator import Orchestrator
from llm.stub import StubLLM

app = FastAPI()
orc = Orchestrator(llm=StubLLM())

@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    return orc.respond(req)
