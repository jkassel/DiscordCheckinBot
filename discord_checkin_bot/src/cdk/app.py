import os
from dotenv import load_dotenv
from aws_cdk import App, Environment
from discord_checkin_bot_stack import DiscordCheckinBotStack

# Load environment variables from .env file
load_dotenv()

app = App()

env = Environment(
    account=os.getenv("AWS_ACCOUNT"),
    region=os.getenv("AWS_REGION"),
)

app_name = os.getenv("APP_NAME")

DiscordCheckinBotStack(
    app, f"{app_name}DiscordCheckinBotStack", env=env, app_name=app_name
)

app.synth()
