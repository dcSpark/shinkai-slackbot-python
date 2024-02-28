from server import create_app
from slack import SlackBot
import uvicorn
import asyncio
from dotenv import load_dotenv
import os
from shinkai_manager import ShinkaiManager
import signal

shutdown_event = asyncio.Event()

def setup_signal_handler() -> None:
    loop = asyncio.get_running_loop()

    print("signal detected")
    for sig in (signal.SIGHUP, signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, shutdown, sig)

def shutdown(sig: signal.Signals) -> None:
    print(f"Received exit signal {sig.name}")

    all_tasks = asyncio.all_tasks()
    tasks_to_cancel = {task for task in all_tasks if task is not asyncio.current_task()}

    for task in tasks_to_cancel:
        task.cancel()
    print(f"Cancelled {len(tasks_to_cancel)} out of {len(all_tasks)} tasks")

    loop = asyncio.get_running_loop()
    loop.stop()  # Stop the loop to ensure all tasks are cancelled

    os._exit(0)

async def main():
    load_dotenv()  # Ensure environment variables are loaded

    setup_signal_handler()

    shinkai_manager = ShinkaiManager(
        encryption_sk=os.getenv("PROFILE_ENCRYPTION_SK"),
        signature_sk=os.getenv("PROFILE_IDENTITY_SK"),
        receiver_pk=os.getenv("NODE_ENCRYPTION_PK"),
        shinkai_name=os.getenv("NODE_NAME"),
        profile_name=os.getenv("PROFILE_NAME"),
        device_name=os.getenv("DEVICE_NAME")
    )

    # Initialize the FastAPI app with the ShinkaiManager instance
    app = create_app(shinkai_manager)

    # Note: uvicorn.run() is blocking, so we use it in a separate thread or use uvicorn's Server programmatically
    config = uvicorn.Config(app=app, host="0.0.0.0", port=3001, reload=True, loop="auto")
    server = uvicorn.Server(config)

    slack_bot = SlackBot()

    # Create a task for shinkai_manager's background operations
    # task = asyncio.create_task(shinkai_manager.get_node_responses()) # use only for testing api without slack
    task = asyncio.create_task(shinkai_manager.get_node_responses(slack_bot=slack_bot))
    task_server = asyncio.create_task(server.serve())

    tasks = []
    tasks.append(task)
    tasks.append(task_server)
    await asyncio.gather(*tasks)

   

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("App was interrupted. Closing.")
    else:
        print("App closed.")