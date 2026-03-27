import time
from fastapi import FastAPI
import asyncio

app = FastAPI()

@app.get("/1")
# This is a coroutine, processed sequentially
async def endpoint1(): 
    '''
    Runs in Main Thread
    No awaitable operation, cannot be paused
    Requests executed sequentially / synchronously
     
    If called twice within the span of 5 seconds, the following steps will be executed in order : 
    1. print hello
    2. wait for 5 seconds
    3. print bye

    < now that the first request is complete, the second request starts >

    4. print hello
    5. wait for 5 seconds
    6. print bye

    '''
    print("hello")
    # Blocking I/O operation ( cannot be await-ed )
    # Function execution cannot be paused
    # Event loop is blocked while waiting for the result
    # Other requests can only be processed, after this completes
    time.sleep(5)
    print("bye")

@app.get("/2")
# This is a coroutine, processed concurrently
async def endpoint2():
    '''
    Runs in Main Thread
    Has awaitable operation, can be paused
    Requests executed asynchronously
    
    If called twice within the span of 5 seconds, the following steps will be executed in order : 
    1. print hello ( from first request )
    2. print hello ( from second request )
    3. print bye ( 5 seconds after first hello )
    4. print bye ( 5 seconds after second hello )

    '''
    print("hello")

    # Non-Blocking I/O operation ( can be await-ed )
    # When await-ing, function execution pauses
    # Event loop can handle other tasks during this time ( like processing other requests )
    await asyncio.sleep(5) 

    print("bye")

@app.get("/3")
# Processed parallelly
def endpoint3():
    '''
    This is executed synchronously. 
    If called twice within the span of 5 seconds, the following steps will be executed in order : 
    1. print hello
    2. wait for 5 seconds
    3. print bye

    < now that the first request is complete, the second request starts >

    4. print hello
    5. wait for 5 seconds
    6. print bye

    '''
    print("hello")
    time.sleep(5)
    print("bye")

# When you run FastAPI application using Uvicorn, it starts a thread called Main thread

# All endpoints defined using "async def" are called coroutines
# All coroutines run in the Event Loop, which runs in the Main Thread

# All endpoints defined using just "def" are normal functions
# These functions run in separate threads from Main Thread

"""
BEST PRACTICES : 
1. Use async def for endpoints with non-blocking I/O operations like : 
    DB query, external API request, asyncio.sleep, 
2. Don't use async def for endpoints with blocking I/O operations
3. Use normal function ( def ) for endpoints with blocking I/O operations : 
    DB Client library which doesn't have await feature
    time.sleep
"""