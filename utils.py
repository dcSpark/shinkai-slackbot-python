import asyncio
import os
import requests
import json 

class PersistentStorage:
    ThreadJobMapping = "ThreadJobMapping"

async def post_data(input: str, path: str) -> dict:
    try:
        url = f"{os.getenv('SHINKAI_NODE_URL')}{path}"
        headers = {'Content-Type': 'application/json'} 
        response = requests.post(url, data=input, headers=headers)
        print(response.text)
        return response.json()
    except Exception as error:
        print(error)
        if hasattr(error, 'response') and hasattr(error.response, 'data') and hasattr(error.response.data, 'error'):
            print("Error during POST request:", error.response.data.error)
        return {"status": "error", "data": "An error occurred during the POST request"}

async def delay(ms: int):
    await asyncio.sleep(ms / 1000)
