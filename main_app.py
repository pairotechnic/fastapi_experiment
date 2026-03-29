# Standard Library Imports
# TODO : Explain this : contextlib, asynccontextmanager, async context manager, FastAPI lifespan pattern
from contextlib import asynccontextmanager 

# Third-Party Library Imports
import aiohttp # non-blocking http requests
from fastapi import FastAPI, HTTPException # Use JSONResponse when you want precise control over the shape of the response
from pydantic import BaseModel

# Local Application Imports

# ------------------------------
# Pydantic Models
# ------------------------------

# Pydantic handles request/response validation
# Classes inheriting from BaseModel automatically validate JSON ( either as incoming request, or outgoing response )
# Raise 422 Unprocessable Entity if the data doesn't match (required fields not passed)

class ChatRequest(BaseModel): 
    message: str
    model: str = "claude-opus-4-6"
    provider: str = "Anthropic"

class ChatResponse(BaseModel):
    id: str
    content: str
    model: str
    provider: str

# ------------------------------
# Lifespan - manages shared aiohttp sessions
# ------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Before yield : Startup: Create the session once
    # After yield : Shutdown: Close it cleanly
    async with aiohttp.ClientSession() as app.state.session:
        yield

    # Explicit version : 
    # app.state.session = aiohttp.ClientSession()
    # yield
    # await app.state.session.close()

app = FastAPI(lifespan=lifespan)

# Uses the Docker compose service name mock-llm
LLM_URL = "http://mock-llm:8001/v1/chat/completions"

# ------------------------------
# Endpoints
# ------------------------------

@app.get("/health")
# Non-blocking coroutine endpoint running on Event Loop
# FastAPI automatically serializes the return dict to JSON
async def health():
    return {"status": "healthy"}

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    payload = {
        "model": request.model,
        "provider": request.provider,
        "messages": [{"role": "user", "content": request.message}]
    }

    # Hands control back to the event loop until response's headers and status code arrive
    async with app.state.session.post(LLM_URL, json=payload) as response: 

        # Don't share the upstream mock llm error status code with the end user, share a readable 502 server error
        if response.status != 200:
            # Hands control back to event loop
            # Control returns here after response body arrives, and event loop gives control back
            error_body = await response.text()
            print(f"LLM error — status: {response.status}, body: {error_body}")
            raise HTTPException(status_code=502, detail="LLM service error")
        
        # Hands control back to event loop, until the full body arrives
        # Headers and body are 2 separate I/O events
        data = await response.json() 

    return ChatResponse(
        id=data["id"],
        content=data["content"],
        model=data["model"],
        provider=data["provider"],
        dummy_field="hello_world" # Extra field will get stripped from response
    )