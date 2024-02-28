# Shinkai Slack bot Python integration

This repository is dedicated to integrating Slack with the Shinkai backend for a Slack bot. It involves setting up environment variables, deploying the service, and configuring Slack app settings to interact with the Shinkai node. The integration allows for sending messages, creating jobs, and receiving responses from the Shinkai node directly within Slack. This setup is particularly useful for teams looking to streamline their workflow by leveraging the capabilities of Shinkai's backend services through Slack's user-friendly interface.

How to start?

```bash
# create virtual environment if one is not created 
python -m venv venv

# setup `venv` to run stuff 
source venv/bin/activate

# install packages 
pip install -r requirements.txt

# make sure to install shinkai_message_pyo3-0.1.6-cp38-abi3-macosx_11_0_arm64.whl lib or compile one dedicated for your OS
pip install shinkai-lib/shinkai_message_pyo3-0.1.6-cp38-abi3-macosx_11_0_arm64.whl 

# in case the lib needs to be reinstalled, use --force-reinstall
pip install shinkai-lib/shinkai_message_pyo3-0.1.6-cp38-abi3-macosx_11_0_arm64.whl --force-reinstall

# to run the service
python main.py

# running tests
pytest test_integration # default testing command
pytest -s test_integration.py # to see logs
pytest -p no:warnings test_integration.py # to hide any warnings (logs won't appear)
```

### Slack setup

In order to be able to have full Slack integration, we need to get details about Slack Application token and setup necessary configurations. Bot requires 2 pieces of information:

1. **Slack bot token (xoxb-)**: To retrieve your Slack bot token, first navigate to the Slack API website and log in to your account. Then, create a new app or select an existing one from your apps list. Under the 'Features' section in the sidebar, click on 'OAuth & Permissions'. Scroll down to the 'Bot Token Scopes' section and add the necessary scopes for your bot. After configuring the scopes, scroll up to the 'OAuth Tokens for Your Workspace' section and click the 'Install to Workspace' button. Follow the prompts to install the app to your workspace, and you will be provided with a bot token starting with `xoxb-``. This token is what you'll use to authenticate your bot with the Slack API.
2. **Slack channel id**, where the bot is going to be installed

## Environment Variables Explanation

The `.env.example` file provides a template for setting up your environment variables. Here's a breakdown of what each variable means:

* `PROFILE_ENCRYPTION_SK`: Secret key for profile encryption.
* `PROFILE_IDENTITY_SK`: Secret key for profile identity.
* `NODE_ENCRYPTION_PK`: Public key for node encryption.

* `PROFILE_NAME`: The name of your profile.
* `DEVICE_NAME`: The name of your device.
* `NODE_NAME`: The name of your node, typically set to `@@localhost.shinkai` for local development.

* `SHINKAI_NODE_URL`: The URL of the Shinkai node. This is typically set to `http://127.0.0.1:9550` for local development.

* `SLACK_BOT_TOKEN`: The token for your Slack bot. This is required for the bot to function.
* `SLACK_SIGNING_SECRET`: The signing secret for your Slack app. This is used to verify that incoming requests from Slack are legitimate. It's available from your Slack app's "Basic Information" page under "App Credentials". **This is optional parameter in case `/slack` endpoint is going to be used. Otherwise, feel free to skip it**

* `PORT`: The port on which your service will run. The default is `3001`.

Make sure to copy `.env.example` to `.env` and fill in the values before running your application.
