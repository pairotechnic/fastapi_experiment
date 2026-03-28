from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uuid

app = FastAPI()

class ChatRequest(BaseModel):
    model: str
    provider: str
    messages: list[dict]

@app.post("/v1/chat/completions", status_code=200)
async def chat(request: ChatRequest):
    # Returns a static response no matter what you send
    # When you return a dict or Pydantic model from a FastAPI endpoint, without specifying a status code,
    # FastAPI defaults to 200 OK
    
    if request.provider == "OpenAI":
        raise HTTPException(status_code=403, detail="This provider is no longer supported")

    return {
        "id": f"mock-response-id-{str(uuid.uuid4())}",
        "model": request.model,
        "provider": request.provider,
        "content": "Success - Mock LLM Response",
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 8
        }
    }

