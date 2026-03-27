import time
from fastapi import FastAPI

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