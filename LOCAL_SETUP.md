# Local Development Setup

## Environment Variables Required

You need to create a `.env` file in your project root with the following variables:

```bash
# Slack App Configuration
SLACK_BOT_TOKEN=your_bot_token_here
SLACK_SIGNING_SECRET=your_signing_secret_here
PORT=3000
```

## How to Get Your Slack Credentials

### 1. Go to Your Slack App Dashboard
- Visit: https://api.slack.com/apps
- Select your Learning Management app

### 2. Get the Bot Token
- Go to **"OAuth & Permissions"** in the left sidebar
- Copy the **"Bot User OAuth Token"** (starts with `xoxb-`)
- This is your `SLACK_BOT_TOKEN`

### 3. Get the Signing Secret
- Go to **"Basic Information"** in the left sidebar
- Under **"App Credentials"**, copy the **"Signing Secret"**
- This is your `SLACK_SIGNING_SECRET`

### 4. Create the .env File
Create a file named `.env` in your project root with:
```
SLACK_BOT_TOKEN=xoxb-your-actual-token-here
SLACK_SIGNING_SECRET=your-actual-signing-secret-here
PORT=3000
```

### 5. Install Dependencies
Before running the app, install the required Python packages:
```bash
pip3 install -r requirements.txt
```

This will install:
- `slack-bolt` - Slack app framework
- `flask` - Web framework
- `gunicorn` - Production server
- `python-dotenv` - Environment variable management
- `requests` - HTTP library

**Note**: The database packages (psycopg2-binary, sqlalchemy, alembic) are commented out in `requirements.txt` since the app uses in-memory storage. If you need PostgreSQL in the future, uncomment those lines and install PostgreSQL development tools first.

### 6. Test the App
Run the app with:
```bash
python app.py
```

The app should start without the token error.

## Troubleshooting

- Make sure the `.env` file is in the same directory as `app.py`
- Ensure there are no spaces around the `=` in the `.env` file
- The bot token should start with `xoxb-`
- The signing secret should be a long string of characters
