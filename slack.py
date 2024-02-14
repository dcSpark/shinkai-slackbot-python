from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import os

class SlackBot:
    def __init__(self, is_testing=False):
        self.is_testing = is_testing or os.getenv("NODE_ENV") == "test"
        self.token = os.getenv("SLACK_BOT_TOKEN", "")
        if not self.is_testing and not self.token:
            raise ValueError("SLACK_BOT_TOKEN env not defined. SLACK_BOT_TOKEN: {}".format(self.token))
        
        self.client = WebClient(token=self.token)

    async def post_message_to_channel(self, channel_id, text):
        try:
            response = await self.client.chat_postMessage(channel=channel_id, text=text)
            return response
        except SlackApiError as e:
            print(f"Error posting message to channel: {e.response['error']}")

    async def post_message_to_thread(self, channel_id, thread_ts, text):
        try:
            response = self.client.chat_postMessage(channel=channel_id, thread_ts=thread_ts, text=text)
            if response["ok"]:
                print(f"Response from the node: {text}; posted to channelId: {channel_id} successfully.")
                print(f"message sent to Slack")
            return response
        except SlackApiError as e:
            print(f"Error posting message to thread: {e.response['error']}")
