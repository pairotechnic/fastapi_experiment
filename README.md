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