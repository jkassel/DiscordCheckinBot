# 📰 Discord Check-in Bot

[![GitHub license](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Build Status](https://github.com/jkassel/DiscordCheckinBot/actions/workflows/deploy.yml/badge.svg)](https://github.com/jkassel/DiscordCheckinBot/actions)
[![AWS CDK](https://img.shields.io/badge/built%20with-AWS%20CDK-orange)](https://aws.amazon.com/cdk/)
[![Python](https://img.shields.io/badge/python-3.11-blue)](https://www.python.org/)

## 🌟 Overview

**Discord Check-in Bot** allows users to **check in** to locations within a Discord server using an intuitive button-based interface. It integrates with **Google Maps API** to provide accurate location-based check-ins.

👉 **Key Features:**
- ✅ **Button-based UI** instead of slash commands.
- 🔖 **Location-based check-ins** with Google Maps integration.
- 🔒 **Secure deployment** using AWS Lambda and API Gateway.
- 🛠 **Built to integrate with DiscordBotShared infrastructure.**

---

## 🔧 Dependency on DiscordBotShared

This bot depends on the **DiscordBotShared** repository, which contains the shared API Gateway and common infrastructure. Before deploying this bot, make sure you have:

1. Cloned and deployed the `DiscordBotShared` repository.
   ```sh
   git clone https://github.com/jkassel/DiscordBotShared.git
   cd DiscordBotShared
   cdk deploy
   ```
2. Ensure that `DiscordBotShared` exports necessary values such as the **API Gateway ID** and **endpoint**, which will be referenced in this bot.

---

## 📂 Project Structure

```
📦 DiscordCheckinBot
├── 💁 src
│   ├── 💁 cdk                # AWS CDK Infrastructure
│   │   ├── app.py           # CDK entry point
│   │   ├── cdk.json         # CDK configuration
│   │   ├── checkin_bot_stack.py  # Defines API Gateway route, Lambda function
│   │   └── outputs.py       # Exports values for dependent repos
│   ├── 💁 lambda             # Lambda function code
│   │   ├── checkin_main.py  # Lambda entry point
│   │   ├── discord_handler.py # Handles Discord interactions
├── 💁 .github/workflows       # CI/CD automation
├── requirements.txt           # Python dependencies
├── README.md                  # Documentation (YOU ARE HERE)
└── Makefile                   # Simplified setup and deployment
```

---

## 🚀 Deployment Guide

### **1⃣ Prerequisites**
- ✅ Python 3.11+ installed ([Download](https://www.python.org/downloads/))
- ✅ AWS CLI installed and configured (`aws configure`)
- ✅ AWS CDK installed:
  ```sh
  npm install -g aws-cdk
  ```
- ✅ [Discord Bot Token](https://discord.com/developers/applications) and API credentials.
- ✅ **Google Maps API Key** for geolocation services.

---

### **2⃣ Installation**
Clone the repository and install dependencies:
```sh
git clone https://github.com/jkassel/DiscordCheckinBot.git
cd DiscordCheckinBot
pip install -r requirements.txt
```

---

### **3⃣ Deploy Shared Infrastructure**
Before deploying `DiscordCheckinBot`, make sure `DiscordBotShared` is **deployed first**, as this bot depends on its shared API Gateway:

```sh
git clone https://github.com/jkassel/DiscordBotShared.git
cd DiscordBotShared
cdk deploy
```

---

### **4⃣ Deploy Check-in Bot to AWS**
```sh
cdk bootstrap
cdk deploy
```

Upon successful deployment, this bot will:
- **Attach to the shared API Gateway** from `DiscordBotShared`.
- **Deploy a Lambda function** for processing check-ins.
- **Export API Gateway route details** for Discord integration.

---

## 🔒 Exports for Dependent Repositories
After deployment, the following values will be available:

| Export Name           | Description |
|----------------------|-------------|
| **`CheckinApiEndpoint`**  | The endpoint for Discord check-ins. |

---

## 🌟 Integrating with Discord
Once deployed, set up your Discord bot:
1. Navigate to the [Discord Developer Portal](https://discord.com/developers/applications).
2. Configure the **Interactions Endpoint URL** using the exported `CheckinApiEndpoint`.
3. Register the bot’s commands and enable **message content intent**.

---

## 🛠 Troubleshooting

| Issue | Solution |
|--------|------------|
| **`ResourceNotFound` when retrieving API Gateway info** | Ensure **DiscordBotShared** is deployed **before** Check-in Bot. |
| **Lambda permissions error** | Verify that the IAM role has `lambda:InvokeFunction` permissions. |
| **Discord interactions not working** | Ensure the **Interactions Endpoint URL** is correctly set in the Discord Developer Portal. |

---

## 💬 Support

Need help? **Join the Discord support server** or open a [GitHub Issue](https://github.com/YOUR_GITHUB_USERNAME/DiscordCheckinBot/issues).

---

## 🚀 Star ⭐ this repo if you found it useful!

