from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class ChatRequest(BaseModel):
    model: str
    messages: list[dict]

class ChatResponse(BaseModel):
    id: str
    content: str

@app.post("/v1/chat/completions")
async def chat(request: ChatRequest):
    # Returns a static response no matter what you send
    return {
        "id": "mock-response-001",
        "content": "This is a static mock LLM response.",
        "model": request.model,
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 8
        }
    }