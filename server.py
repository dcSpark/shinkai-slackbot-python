from datetime import datetime, time
from fastapi import FastAPI, Request, HTTPException, status, Depends
from starlette.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from shinkai_manager import ShinkaiManager, SlackJobAssigned
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from slack_sdk.signature import SignatureVerifier
from dotenv import load_dotenv
import os
import hashlib
import hmac
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
import json

from utils import load_thread_job_mapping, save_thread_job_mapping

class SlackEventApiRequestBodyContent(BaseModel):
    type: str
    client_msg_id: str
    text: str
    user: str
    ts: str
    blocks: List[Dict[str, Any]]
    team: str
    channel: str
    event_ts: str
    channel_type: str
    thread_ts: Optional[str] = None

load_dotenv()

slack_client = WebClient(token=os.getenv("SLACK_BOT_TOKEN"))
signature_verifier = SignatureVerifier(signing_secret=os.getenv("SLACK_SIGNING_SECRET"))

app = FastAPI()


@app.on_event("shutdown")
async def app_shutdown():
    from main import shutdown_event
    shutdown_event.set()

# Global variable to store thread to job mapping (this can be initialized to {} or loaded from file if file was created)
thread_job_mapping: Dict[str, str] = load_thread_job_mapping()


# Modify the FastAPI app initialization to accept ShinkaiManager instance:
def create_app(shinkai_manager: ShinkaiManager):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.state.shinkai_manager = shinkai_manager
    init_routes(app)
    return app

def init_routes(app: FastAPI):
    @app.post("/slack/events")
    async def slack_events(request: Request):
        try:
            json_data = await request.json()

            # URL Verification (important for slack setup)
            if "challenge" in json_data:
                return {"challenge": json_data["challenge"]}
            
            global seen_event_times
            if 'seen_event_times' not in globals():
                seen_event_times = set()

            event_time = json_data.get("event_time")
            if event_time in seen_event_times:
                print(f"Duplicate event detected: {event_time}, skipping processing.")
                return JSONResponse(content={"status": "ok"}, status_code=200)
            else:
                seen_event_times.add(event_time)
                print(f"Processing new event: {event_time}")

            event = json_data.get("event", {})
            if event.get("type") == "app_mention" and "text" in event and json_data.get("api_app_id") == os.getenv("SLACK_APP_ID"):
                # cleanup the message (there's <@USER_APP_ID> as a prefix added each time we send something)
                message = event.get("text", "").replace("<@([A-Z0-9]+)>", "")
                print(f"Extracted message: {message}")

                if message:
                    thread_id = event.get("thread_ts") or event.get("ts")

                    if thread_id is None:
                        raise ValueError("Couldn't identify thread for reply. thread_ts: {}".format(thread_id))

                    existing_job_id = thread_job_mapping.get(thread_id)
                    if existing_job_id:
                        print(f"Thread {thread_id} already has existing job id assigned: {existing_job_id}")
                        job_id = existing_job_id
                    else:
                        # create shinkai job
                        print("Creating job id...")
                        job_id = await app.state.shinkai_manager.create_job("main/agent/my_gpt")

                        # assign job id for the future
                        thread_job_mapping[thread_id] = job_id

                        # make thread_job_mapping persistent update it here
                        save_thread_job_mapping(thread_job_mapping)
                        
                    print(f"### Job ID: {job_id}")

                    # send job message to the node
                    answer = await app.state.shinkai_manager.send_message(message, job_id)

                    app.state.shinkai_manager.active_jobs.append(SlackJobAssigned(message=message, shinkai_job_id=job_id, slack_thread_id=thread_id, slack_channel_id=event.get("channel"), start_timestamp=int(datetime.now().timestamp())))
                    
                    print(f"### Answer: {answer}")
                else:
                    raise ValueError(f"{message} was not provided. Nothing to pass to the node.")
            return JSONResponse(content={"status": "ok"}, status_code=200)
        except Exception as e:
            print(e)
            return JSONResponse(content={"status": "error", "message": str(e)}, status_code=400)

    @app.get("/health")
    async def health_check():
        return {"status": "success", "message": "Shinkai Slack backend is up and running."}



