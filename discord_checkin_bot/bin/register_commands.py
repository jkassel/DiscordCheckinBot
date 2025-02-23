import os
import requests
from dotenv import load_dotenv


# Load environment variables from .env file
load_dotenv()


def register_checkin_slash_command(bot_token: str, app_id: str):
    """
    Registers (or updates) the /checkin slash command with auto-complete
    for the 'location' argument, plus optional 'message' and 'photo' arguments.

    :param bot_token: The Discord bot token (raw token, no "Bot " prefix).
    :param app_id:    The application ID from the Discord Developer Portal.
    """

    url = f"https://discord.com/api/v10/applications/{app_id}/commands"

    # Define the slash command JSON
    # Note: "guild_id" can be added in your request URL if you want
    # to register the command as a guild-specific command (for faster updates).
    command_data = {
        "name": "checkin",
        "description": "Check in to a location, with optional custom message and photos!",
        "options": [
            {
                "name": "location",
                "description": "Where are you?",
                "type": 3,  # STRING
                "autocomplete": True,  # Auto-complete enabled
                "required": False,
            },
            {
                "name": "message",
                "description": "Add a custom message",
                "type": 3,  # STRING
                "required": False,
            },
            {
                "name": "photo",
                "description": "Attach an image",
                "type": 11,  # ATTACHMENT
                "required": False,
            },
        ],
    }

    headers = {"Authorization": f"Bot {bot_token}", "Content-Type": "application/json"}

    response = requests.post(url, headers=headers, json=command_data)

    if response.status_code in (200, 201):
        print("✅ Successfully registered (or updated) the /checkin command!")
    else:
        print(f"❌ Failed to register the command. Status: {response.status_code}")
        print("Response:", response.text)


if __name__ == "__main__":
    DISCORD_BOT_TOKEN = os.environ.get('DISCORD_BOT_TOKEN')
    DISCORD_APP_ID = os.environ.get('DISCORD_APP_ID')

    if not DISCORD_BOT_TOKEN or not DISCORD_APP_ID:
        print("❌ Missing DISCORD_BOT_TOKEN or DISCORD_APP_ID environment variables.")
    else:
        register_checkin_slash_command(DISCORD_BOT_TOKEN, DISCORD_APP_ID)
