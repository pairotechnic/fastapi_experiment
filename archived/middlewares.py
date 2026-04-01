# Standard Library Imports
import asyncio
import time

# Third-Party Library Imports
from fastapi import Request 
from fastapi.responses import JSONResponse

# Local Application Imports
from main_app import app
from config import (
    RATE_LIMIT_REQUESTS,
    RATE_LIMIT_WINDOW_SECONDS,
    logger
)

@app.middleware("http")
async def single_worker_rate_limiter(request: Request, call_next):
    ip = request.client.host

    
    async with app.state.rate_limit_lock:
        now = time.time()
        window_start = now - RATE_LIMIT_WINDOW_SECONDS
        # Drop timestamps outside the current window
        app.state.request_log[ip] = [t for t in app.state.request_log[ip] if t > window_start]

        if len(app.state.request_log[ip]) >= RATE_LIMIT_REQUESTS:
            logger.warning(f"Rate limit exceeded for IP : {ip}")
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests"}
            )
        
        # Simulate async work between check and append
        # e.g. looking up IP in a database, or a Redis read
        await asyncio.sleep(0)  # yields control back to event loop
        
        # Record this request
        app.state.request_log[ip].append(now)

    return await call_next(request)