import os
import boto3
import json
import nacl.signing
import nacl.exceptions
import requests
import urllib.parse

# =====================
#   LOGGING SETUP
# =====================
LOG_LEVELS = {"DEBUG": 10, "INFO": 20, "WARN": 30, "ERROR": 40}
DEFAULT_LOG_LEVEL = "INFO"

CURRENT_LOG_LEVEL = os.getenv("LOG_LEVEL", DEFAULT_LOG_LEVEL).upper()
CURRENT_LOG_LEVEL_NUM = LOG_LEVELS.get(CURRENT_LOG_LEVEL, LOG_LEVELS[DEFAULT_LOG_LEVEL])


def log(message: str, level: str = "INFO"):
    level = level.upper()
    if LOG_LEVELS.get(level, 0) >= CURRENT_LOG_LEVEL_NUM:
        print(f"[{level}] {message}")


def log_return(response_dict, level: str = "DEBUG"):
    """Helper to log the final return from the Lambda."""
    # e.g. {"statusCode": 200, "body": "..."}
    log(f"Completed with {json.dumps(response_dict)}", level)


# =====================
#   SECRETS & CONFIG
# =====================
secrets_client = boto3.client("secretsmanager")
discord_secret_arn = os.getenv("DISCORD_BOT_SECRET_ARN")
google_secret_arn = os.getenv("GOOGLE_MAPS_SECRET_ARN")


def get_discord_secrets():
    log("Fetching Discord secrets", "DEBUG")
    response = secrets_client.get_secret_value(SecretId=discord_secret_arn)
    secret = json.loads(response["SecretString"])
    return secret.get("token"), secret.get("appId"), secret.get("publicKey")


TOKEN, APP_ID, PUBLIC_KEY = get_discord_secrets()


def get_google_secrets():
    log("Fetching Google secrets from AWS Secrets Manager", "DEBUG")
    response = secrets_client.get_secret_value(SecretId=google_secret_arn)
    secret = json.loads(response["SecretString"])
    return secret.get("GOOGLE_MAPS_API_KEY")


GOOGLE_MAPS_API_KEY = get_google_secrets()


# =====================
#   HELPER METHODS
# =====================
def verify_signature(event):
    signature = event["headers"].get("x-signature-ed25519", "")
    timestamp = event["headers"].get("x-signature-timestamp", "")
    body = event.get("body", "")

    log("Verifying request signature", "DEBUG")
    try:
        verify_key = nacl.signing.VerifyKey(
            PUBLIC_KEY, encoder=nacl.encoding.HexEncoder
        )
        verify_key.verify(f"{timestamp}{body}".encode(), bytes.fromhex(signature))
        log("Signature verified successfully", "DEBUG")
        return True
    except nacl.exceptions.BadSignatureError:
        log("Signature verification failed", "WARN")
        return False


def get_location_suggestions(input_text: str) -> list:
    """Calls the Places Autocomplete API for suggestions based on user input."""
    if not input_text:
        log("No input text for auto-complete, returning empty list", "DEBUG")
        return []
    url = "https://maps.googleapis.com/maps/api/place/autocomplete/json"
    params = {
        "key": GOOGLE_MAPS_API_KEY,
        "input": input_text,
        # Removing types/components so we get all results (addresses, establishments, etc.)
    }
    log(f"Calling Google Places with input='{input_text}'", "DEBUG")

    response = requests.get(url, params=params)
    log(
        f"Google Places status={response.status_code}, body={response.text[:200]}",
        "DEBUG",
    )
    data = response.json()
    predictions = data.get("predictions", [])
    suggestions = [p["description"] for p in predictions[:5]]
    log(f"Parsed suggestions: {suggestions}", "DEBUG")
    return suggestions


def send_interaction_response(interaction_id, interaction_token, message_data):
    """Sends a response to the Discord interaction using the callback URL."""
    url = f"https://discord.com/api/v10/interactions/{interaction_id}/{interaction_token}/callback"
    headers = {"Content-Type": "application/json"}

    log("Sending interaction response to Discord", "DEBUG")
    resp = requests.post(url, headers=headers, json=message_data)
    log(f"Discord response status={resp.status_code}, body={resp.text}", "DEBUG")


# =====================
#   MAIN LAMBDA
# =====================
def lambda_handler(event, context):
    log(f"Received event: {json.dumps(event)}", "DEBUG")

    # 1. Verify signature
    if not verify_signature(event):
        resp_dict = {"statusCode": 401, "body": "invalid request signature"}
        log_return(resp_dict, "WARN")
        return resp_dict

    body = json.loads(event["body"])
    interaction_type = body.get("type")
    interaction_id = body.get("id")
    interaction_token = body.get("token")

    log(f"Interaction type={interaction_type}, ID={interaction_id}", "DEBUG")

    # 2. PING
    if interaction_type == 1:
        resp_dict = {"statusCode": 200, "body": json.dumps({"type": 1})}
        log_return(resp_dict)
        return resp_dict

    # 3. AUTO-COMPLETE
    if interaction_type == 4:
        log("Handling auto-complete request", "DEBUG")
        options = body["data"].get("options", [])
        choices = []
        if options:
            partial_text = options[0].get("value", "")
            suggestions = get_location_suggestions(partial_text)
            choices = [{"name": s, "value": s} for s in suggestions]

        response_data = {"type": 8, "data": {"choices": choices}}
        resp_dict = {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(response_data),
        }
        log(f"Returning auto-complete choices: {choices}", "DEBUG")
        log_return(resp_dict)
        return resp_dict

    # 4. SLASH COMMAND
    if interaction_type == 2:
        log("Handling slash command submission", "DEBUG")
        data = body.get("data", {})
        options = data.get("options", [])

        if options:
            # Extract user input
            location_value = None
            message_value = ""
            for opt in options:
                if opt["name"] == "location":
                    location_value = opt["value"]
                elif opt["name"] == "message":
                    message_value = opt["value"]

            # If we have a location, generate embed with static map
            if location_value:
                log(
                    f"User provided location={location_value}, message={message_value}",
                    "DEBUG",
                )
                display_name = (
                    body["member"].get("nick") or body["member"]["user"]["username"]
                )

                # Build the static map URL
                encoded_location = urllib.parse.quote(location_value)
                map_url = (
                    f"https://maps.googleapis.com/maps/api/staticmap?"
                    f"center={encoded_location}"
                    f"&zoom=15"
                    f"&size=600x300"
                    f"&markers=color:red|{encoded_location}"
                    f"&key={GOOGLE_MAPS_API_KEY}"
                )

                # Build the embed
                embed = {
                    "title": "📍 Check-In Complete!",
                    "color": 0x5865F2,  # Discord 'blurple'
                    "description": (
                        f"**Location**: {location_value}\n"
                        f"**Message**: {message_value if message_value else '*No message provided*'}\n\n"
                        f"[View on Google Maps]"
                        f"(https://www.google.com/maps/search/?api=1&query={encoded_location})"
                    ),
                    "image": {"url": map_url},
                    "footer": {"text": f"Checked in by {display_name}"},
                }

                # If the user attached images, include them as additional images in the embed
                attachments = body.get("attachments", [])
                embeds = [embed]
                for att in attachments[:4]:
                    embeds.append({"image": {"url": att["url"]}})

                send_interaction_response(
                    interaction_id,
                    interaction_token,
                    {
                        "type": 4,
                        "data": {
                            "content": f"{display_name} just checked in!",
                            "embeds": embeds,
                        },
                    },
                )
                resp_dict = {"statusCode": 200, "body": ""}
                log_return(resp_dict)
                return resp_dict

        # If no location parameter was provided, show an instruction message
        log("No location argument provided; returning instructions", "DEBUG")
        send_interaction_response(
            interaction_id,
            interaction_token,
            {
                "type": 4,
                "data": {
                    "content": (
                        "It looks like you didn't provide a location.\n\n"
                        "**Usage:** `/checkin location:<place> [message:<text>]`\n"
                        'For example: `/checkin location:"Madison Square Garden" message:"Having a great time!"`'
                    ),
                    "flags": 64,  # This makes the message ephemeral (visible only to user)
                },
            },
        )
        resp_dict = {"statusCode": 200, "body": ""}
        log_return(resp_dict)
        return resp_dict

    # 5. Fallback - unhandled interaction types
    log("Unhandled interaction type, returning 400", "WARN")
    resp_dict = {
        "statusCode": 400,
        "body": json.dumps({"error": "Unhandled interaction type"}),
    }
    log_return(resp_dict, "WARN")
    return resp_dict
