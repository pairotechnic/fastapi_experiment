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

The Event Loop's Ready Queue
This is the event loop's main queue of coroutines that are ready to run right now. When a coroutine hits any await, it gets removed from the running state. If the thing it's awaiting is already resolved (like asyncio.sleep(0) which resolves immediately), it gets put back at the end of the ready queue. The event loop always picks from the front of this queue.

The Lock's Waiter Queue
This is internal to the asyncio.Lock object. When a coroutine tries to async with lock and the lock is already held, it doesn't go back to the event loop's ready queue — it parks itself in the lock's private waiter queue. It is not runnable. It will not be scheduled. It just waits there until the lock is released.

When the lock is released, it takes the first waiter off its own queue and moves it to the event loop's ready queue. Only then does it become runnable again.