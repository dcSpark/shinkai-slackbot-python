from server import create_app
from slack import SlackBot
import uvicorn
import asyncio
from dotenv import load_dotenv
import os
from shinkai_manager import ShinkaiManager
import signal


async def main():
    load_dotenv()  # Ensure environment variables are loaded

    shinkai_manager = ShinkaiManager(
        encryption_sk=os.getenv("ENCRYPTION_SK"),
        signature_sk=os.getenv("SIGNATURE_SK"),
        receiver_pk=os.getenv("RECEIVER_PK"),
        shinkai_name=os.getenv("NODE_NAME"),
        profile_name=os.getenv("PROFILE_NAME"),
        device_name=os.getenv("DEVICE_NAME")
    )

    # Initialize the FastAPI app with the ShinkaiManager instance
    app = create_app(shinkai_manager)

    # Since we're inside an async function, let's use asyncio to run the Uvicorn server
    # Note: uvicorn.run() is blocking, so we use it in a separate thread or use uvicorn's Server programmatically
    config = uvicorn.Config(app=app, host="0.0.0.0", port=3001, reload=True)
    server = uvicorn.Server(config)

    slack_bot = SlackBot()

    # Create a task for shinkai_manager's background operations
    # task = asyncio.create_task(shinkai_manager.get_node_responses()) # use only for testing api without slack
    task = asyncio.create_task(shinkai_manager.get_node_responses(slack_bot=slack_bot))

    # Run both the server and the background task concurrently
    await asyncio.gather(server.serve(), task)

    loop = asyncio.get_running_loop()
    for sig in [signal.SIGINT, signal.SIGTERM]:
        loop.add_signal_handler(sig, lambda: asyncio.create_task(shutdown(sig)))


async def shutdown(signal):
    print(f"Received exit signal {signal.name}...")
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    [task.cancel() for task in tasks]

    print("Cancelling outstanding tasks")
    await asyncio.gather(*tasks, return_exceptions=True)
    asyncio.get_event_loop().stop()
    print("Shutdown complete.")

if __name__ == "__main__":
    asyncio.run(main())