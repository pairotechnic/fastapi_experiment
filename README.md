# FastAPI experiment

Explore the following : 
- FastAPI, 
- asynchronous code, 
- multi-threading, 
- concurrency, 
- race conditions, 
- resource locking, 

TODO : 
AsyncIO vs Threading vs Multiprocessing

FastAPI runs on an event loop - A single thread that manages many concurrent operations by switching between them whenever one is waiting on I/O. When a coroutine hits an 'await', it hands control back to the event loop, which can then run other coroutines while the original one waits

When you return a dict or Pydantic model from a FastAPI endpoint, without specifying a status code, FastAPI defaults to 200 OK

asyncio.Lock is per event loop, so it must live on app.state, not as a global variable when running multiple workers

The event loop processes all pending work before returning to any sleeping coroutine.
The event loop has a queue. await puts your coroutine at the back of the queue. asyncio.sleep(0) puts you at the back once. By the time you get back to the front, everyone else has already had their turn in round 1 — and passed the check.