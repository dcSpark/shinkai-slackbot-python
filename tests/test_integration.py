import asyncio
import pytest
from fastapi.testclient import TestClient
from server import create_app
from shinkai_manager import ShinkaiManager
from slack import SlackBot
from utils import delay
import os

shinkai_manager = ShinkaiManager(
    encryption_sk=os.getenv("ENCRYPTION_SK"),
    signature_sk=os.getenv("SIGNATURE_SK"),
    receiver_pk=os.getenv("RECEIVER_PK"),
    shinkai_name=os.getenv("NODE_NAME"),
    profile_name=os.getenv("PROFILE_NAME"),
    device_name=os.getenv("DEVICE_NAME")
)

client = TestClient(create_app(shinkai_manager))

@pytest.mark.asyncio
async def test_health_check_endpoint():
    # Trigger health check endpoint
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "success", "message": "Shinkai Slack backend is up and running."}

@pytest.mark.asyncio
async def test_trigger_slack_endpoint_with_ai_prompts():
    prompts = [
        "What is the meaning of life?",
        "Explain the theory of relativity",
    ]

    task = asyncio.create_task(shinkai_manager.get_node_responses())

    pending_messages_after = len(shinkai_manager.active_jobs)
    for prompt in prompts:
        pending_messages_before = len(shinkai_manager.active_jobs)
        await shinkai_manager.create_job_and_send(prompt)

        pending_messages_after = len(shinkai_manager.active_jobs)

    await delay(30)

    print(pending_messages_before)
    print(pending_messages_after)

    # Ensure that the number of pending messages is not increasing unexpectedly
    assert pending_messages_before <= pending_messages_after
    task.cancel()
    loop = asyncio.get_running_loop()
    loop.stop()     



