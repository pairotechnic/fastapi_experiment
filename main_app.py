# Standard Library Imports
import asyncio
from collections import defaultdict
from contextlib import asynccontextmanager 
import json
import time

# Third-Party Library Imports
import aiohttp # non-blocking http requests
from fastapi import FastAPI, HTTPException, Request 
from fastapi.responses import JSONResponse # Use JSONResponse when you want precise control over the shape of the response
from pydantic import BaseModel
import redis.asyncio as aioredis

# Local Application Imports
from config import (
    LLM_URL, 
    LLM_TIMEOUT_SECONDS, 
    DEFAULT_MODEL, 
    DEFAULT_PROVIDER, 
    RATE_LIMIT_REQUESTS,
    RATE_LIMIT_WINDOW_SECONDS,
    REDIS_URL,
    logger
)
from helpers import trace_exception_hierarchy


# ------------------------------
# Global Variables
# ------------------------------

LLM_TIMEOUT = aiohttp.ClientTimeout(total=LLM_TIMEOUT_SECONDS)

# ------------------------------
# Pydantic Models
# ------------------------------

# Pydantic handles request/response validation
# Classes inheriting from BaseModel automatically validate JSON ( either as incoming request, or outgoing response )
# Raise 422 Unprocessable Entity if the data doesn't match (required fields not passed)

class ChatRequest(BaseModel): 
    message: str
    model: str = DEFAULT_MODEL
    provider: str = DEFAULT_PROVIDER
    speed: str = ""

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
        # Rate Limiting State
        app.state.request_log = defaultdict(list)
        # app.state.rate_limit_lock = asyncio.Lock() # Locks a resource away from other coroutines on same worker, not across workers
        app.state.redis = aioredis.from_url(REDIS_URL)
        logger.info(f"LLM_TIMEOUT_SECONDS loaded as: {LLM_TIMEOUT_SECONDS}")
        yield

    # Explicit version : 
    # app.state.session = aiohttp.ClientSession()
    # yield
    # await app.state.session.close()

app = FastAPI(lifespan=lifespan)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    end = time.time()
    duration_ms = (end-start) * 1000
    logger.info(
        f"{request.method} {request.url.path} "
        f"-> {response.status_code} "
        f"({duration_ms:.1f}ms)"
    )
    return response

@app.middleware("http")
async def rate_limiter(request: Request, call_next):
    ip = request.client.host
    key = f"rate_limit:{ip}"
    now = time.time()
    window_start = now - RATE_LIMIT_WINDOW_SECONDS

    # Execute atomically in Redis - all 4 commands sent as one pipeline
    async with app.state.redis.pipeline(transaction=True) as pipe :
        # 1. Remove timestamps outside the current window
        await pipe.zremrangebyscore(key, 0, window_start)

        # 2. Count remaining requests in window
        await pipe.zcard(key)

        # 3. Add current request with timestamp as score
        await pipe.zadd(key, {str(now): now})

        # 4. Set expiry so keys don't linger forever
        await pipe.expire(key, RATE_LIMIT_WINDOW_SECONDS)
        
        results = await pipe.execute()

    requests_count = results[1] # zcard result

    if requests_count >= RATE_LIMIT_REQUESTS: # since count is retrieved before adding current request
        logger.warning(f"Rate limit exceeded for IP: {ip}")
        return JSONResponse(
            status_code=429,
            content={"detail": "Too many requests"}
        )
    
    return await call_next(request)


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
    logger.info("Entered the /chat endpoint")
    payload = {
        "model": request.model,
        "provider": request.provider,
        "messages": [{"role": "user", "content": request.message}],
        "speed": request.speed
    }

    # Network-level failure - mock LLM is down, DNS fails, connection refused, timeout
    try :
        # Hands control back to the event loop until response's headers and status code arrive
        async with app.state.session.post(LLM_URL, json=payload, timeout=LLM_TIMEOUT) as response: 

            # Don't share the upstream mock llm error status code with the end user, share a readable 502 server error
            if response.status != 200:
                # Hands control back to event loop
                # Control returns here after response body arrives, and event loop gives control back
                error_body = await response.text()
                logger.error(f"LLM error — status: {response.status}, body: {error_body}")
                raise HTTPException(status_code=502, detail="LLM service error")
            
            # Hands control back to event loop, until the full body arrives
            # Headers and body are 2 separate I/O events
            try :
                data = await response.json()
            except aiohttp.ContentTypeError as e:
                logger.error(f"LLM response Content-Type header isn't application/json")
                raise HTTPException(status_code=502, detail="LLM returned invalid response - invalid headers")
            except json.JSONDecodeError as e:
                logger.error(f"LLM response header claims JSON but the body is malformed")
                raise HTTPException(status_code=502, detail="LLM returned invalid response - malformed body")
            except Exception as e:
                logger.error(f"LLM returned invalid JSON: {e}")
                trace_exception_hierarchy(e)
                raise HTTPException(status_code=502, detail="LLM returned invalid response")
            
    except HTTPException:
        raise # Let FastAPI handle these - don't swallow them in the outer except
    
    except aiohttp.ClientConnectionError as e:
        logger.error(f"Could not reach LLM - connection error: {e}")
        raise HTTPException(status_code=503, detail="LLM service unavailable")
    
    except TimeoutError as e:
        logger.error(f"LLM request timed out: {e}")
        trace_exception_hierarchy(e)
        raise HTTPException(status_code=504, detail="LLM service timed out")
    
    except Exception as e:
        logger.error(f"Unexpected error calling LLM: {e}")
        trace_exception_hierarchy(e)
        raise HTTPException(status_code=500, detail="Internal Server Error")

    # LLM returned JSON but is missing expected fields
    try :
        return ChatResponse(
            id=data["id"],
            content=data["content"],
            model=data["model"],
            provider=data["provider"],
            dummy_field="hello_world" # Extra field will get stripped from response
        )
    except KeyError as e:
        logger.error(f"LLM response missing expected field: {e}")
        raise HTTPException(status_code=502, detail="Unexpected LLM response shape")