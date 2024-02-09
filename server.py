from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from slack_sdk.signature import SignatureVerifier
from dotenv import load_dotenv
import os
import hashlib
import hmac
from typing import Optional, Dict, Any, List
from pydantic import BaseModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

@app.post("/slack/events")
async def slack_events(request: Request):

    # TODO: implement challenge & events handling for Slack mentions
    return {"status": "success", "message": "Shinkai Slack backend is up and running."}

@app.get("/health")
async def health_check():
    # TODO: verify node availability
    return {"status": "success", "message": "Shinkai Slack backend is up and running."}

# wip - endpoint to make sure basic node operations work
@app.get("/create-and-send")
async def create_and_send():
    from shinkai_manager import ShinkaiManager

    shinkai_manager = ShinkaiManager(
        encryption_sk=os.getenv("ENCRYPTION_SK"),
        signature_sk=os.getenv("SIGNATURE_SK"),
        receiver_pk=os.getenv("RECEIVER_PK"),
        shinkai_name=os.getenv("NODE_NAME"),
        profile_name=os.getenv("PROFILE_NAME"),
        device_name=os.getenv("DEVICE_NAME")
    )

    job_id = await shinkai_manager.create_job_and_send(message="Who are you?")
    if job_id:
        return {"status": "success", "message": f"Job {job_id} created and message sent."}
    else:
        return {"status": "error", "message": "Failed to create job and send message."}
