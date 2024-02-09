from typing import List, Optional, Dict, Any
import asyncio
import json
from uuid import uuid4
from utils import delay, post_data
from datetime import datetime
# from .slack import SlackBot
from shinkai_message_pyo3 import (
    PyShinkaiMessageBuilder,
    PyShinkaiMessage,
    PyJobScope,
    PyMessageSchemaType
)

class SlackJobAssigned:
    def __init__(self, message: str, shinkai_job_id: str, start_timestamp: Optional[int] = None, slack_channel_id: Optional[str] = None, slack_thread_id: Optional[str] = None):
        self.message = message
        self.shinkai_job_id = shinkai_job_id
        self.start_timestamp = start_timestamp
        self.slack_channel_id = slack_channel_id
        self.slack_thread_id = slack_thread_id

class JobAnalytics:
    def __init__(self, job_id: str, message: str, executed_timestamp: int, node_response: Optional[str] = None, id: Optional[str] = None):
        self.job_id = job_id
        self.message = message
        self.executed_timestamp = executed_timestamp
        self.node_response = node_response
        self.id = id or str(uuid4())

class ArchiveJobsAnalytics:
    def __init__(self, parent_job: JobAnalytics, following_jobs: List[JobAnalytics]):
        self.parent_job = parent_job
        self.following_jobs = following_jobs

class ShinkaiManager:
    def __init__(self, encryption_sk: str, signature_sk: str, receiver_pk: str, shinkai_name: str, profile_name: str, device_name: str):
        print("--------------------------------------------------")
        print("ShinkaiManager Parameters (excluding keys):")
        print("Shinkai Name:", shinkai_name)
        print("Profile Name:", profile_name)
        print("Device Name:", device_name)
        print("--------------------------------------------------")

        # in python implementation we pass all keys as string
        self.encryption_secret_key = encryption_sk
        self.signature_secret_key = signature_sk
        self.receiver_public_key = receiver_pk

        self.shinkai_name = shinkai_name
        self.profile_name = profile_name
        self.device_name = device_name

        self.active_jobs: List[SlackJobAssigned] = []
        self.archive_jobs_analytics: Optional[List[ArchiveJobsAnalytics]] = []

    async def build_job_message(self, message_content: str, job_id: str) -> Any:
        return await PyShinkaiMessageBuilder.job_message(
            job_id,
            message_content,
            "",
            "",
            self.encryption_secret_key,
            self.signature_secret_key,
            self.receiver_public_key,
            self.shinkai_name,
            self.profile_name,
            self.shinkai_name,
            ""
        )

    async def build_create_job(self, agent: str) -> PyShinkaiMessage:

        try:
            # simple job_creation creates message that is unencrypted (commented for now, to be removed)
            # job_scope = PyJobScope()
            # return PyShinkaiMessageBuilder.job_creation(
            #     self.encryption_secret_key,
            #     self.signature_secret_key,
            #     self.receiver_public_key,
            #     job_scope,
            #     False,
            #     self.shinkai_name,
            #     self.profile_name,
            #     self.shinkai_name,
            #     agent
            # )

            # create custom shinkai message has default encryption using DiffieHellmanChaChaPoly1305
            schema = PyMessageSchemaType("JobMessageSchema")
            return PyShinkaiMessageBuilder.create_custom_shinkai_message_to_node(
                self.encryption_secret_key,
                self.signature_secret_key,
                self.receiver_public_key,
                "message1",
                self.shinkai_name,
                "",
                self.shinkai_name,
                agent,
                "",
                schema
            )

        except Exception as e:
            print(f"Error on job_creation: {str(e)}")
        return None

    async def send_message(self, content: str, job_id: str) -> Any:
        message_job = await self.build_job_message(content, job_id)
        resp = await post_data(message_job, "/v1/job_message")
        if resp["status"] == "success":
            return resp["data"]
        else:
            raise Exception(f"Job creation failed:: {resp}")

    # commented code to be fixed
    # async def get_messages(self, job_id: str) -> str:
    #     try:
    #         inbox = PyInboxName.get_job_inbox_name_from_params(job_id).value
    #         message = await self.build_get_messages_for_inbox(inbox)
    #         resp = await post_data(message, "/v1/last_messages_from_inbox")
    #         if len(resp["data"]) == 1:
    #             print("There's no answer available yet.")
    #             return ""
    #         latest_message = resp["data"][-1]
    #         is_job_message = latest_message["body"]["unencrypted"]["message_data"]["unencrypted"]["message_content_schema"] == MessageSchemaType.JobMessageSchema and latest_message["body"]["unencrypted"]["internal_metadata"]["sender_subidentity"] == ""
    #         if is_job_message:
    #             parsed_message = json.loads(latest_message["body"]["unencrypted"]["message_data"]["unencrypted"]["message_raw_content"])
    #             return parsed_message.get("content", "")
    #     except Exception as e:
    #         print(f"Error getting messages for job {job_id}: {str(e)}")
    #     return ""

    async def create_job(self, agent: str) -> str:

        job_message = await self.build_create_job(agent)

        print(job_message)

        endpoint_job = "/v1/create_job"
        resp = await post_data(job_message, endpoint_job)
        print(resp)
        if resp["status"] == "success":
            return resp["data"]
        else:
            raise Exception(f"Job creation failed: {resp}")

    # async def get_node_responses(self, slack_bot: Optional[SlackBot] = None) -> Optional[str]:
    #     while True:
    #         if not self.active_jobs:
    #             await asyncio.sleep(1)
    #             continue
    #         print(f"Number of active jobs awaiting for response: {len(self.active_jobs)}")
    #         for job in self.active_jobs:
    #             try:
    #                 node_response = await self.get_messages(job.shinkai_job_id)
    #                 if node_response:
    #                     if slack_bot:
    #                         slack_message_response = await slack_bot.post_message_to_thread(job.slack_channel_id, job.slack_thread_id, node_response)
    #                         if slack_message_response["ok"]:
    #                             self.active_jobs = [j for j in self.active_jobs if j.shinkai_job_id != job.shinkai_job_id]
    #                             job_analytics = JobAnalytics(job.shinkai_job_id, job.message, int((time.time() - (job.start_timestamp or 0)) / 1000), node_response)
    #                             print(job_analytics)
    #                             existing_parent_index = next((i for i, analytics in enumerate(self.archive_jobs_analytics) if analytics.parent_job.job_id == job.shinkai_job_id), -1)
    #                             if existing_parent_index != -1:
    #                                 self.archive_jobs_analytics[existing_parent_index].following_jobs.append(job_analytics)
    #                             else:
    #                                 self.archive_jobs_analytics.append(ArchiveJobsAnalytics(parent_job=job_analytics, following_jobs=[]))
    #             except Exception as e:
    #                 print(f"Response for job_id: {job.shinkai_job_id} not available: {str(e)}")
    #         await asyncio.sleep(1)

    async def create_job_and_send(self, message: str, existing_job_id: Optional[str] = None) -> Optional[str]:
        agent = "main/agent/my_gpt"
        try:
            if existing_job_id is None:
                job_id = await self.create_job(agent)
            else:
                job_id = existing_job_id
            print(f"### Job ID: {job_id}")
            answer = await self.send_message(message, job_id)
            self.active_jobs.append(SlackJobAssigned(message=message, shinkai_job_id=job_id, start_timestamp=int(datetime.now().timestamp())))
            print(f"### Answer: {answer}")
            return job_id
        except Exception as e:
            print(f"Error creating job and sending message: {str(e)}")
        return None
