import time
from fastapi import FastAPI
import asyncio

app = FastAPI()

@app.get("/1")
async def endpoint1():
    '''This is executed synchronously. 
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

@app.get("/2")
async def endpoint2():
    '''This is executed asynchronously, when the requests come from 2 different browsers. 
    If called twice within the span of 5 seconds, the following steps will be executed in order : 
    1. print hello ( from first request )
    2. print hello ( from second request )
    3. print bye ( 5 seconds after first hello )
    4. print bye ( 5 seconds after second hello )

    '''
    print("hello")
    await asyncio.sleep(5)
    print("bye")