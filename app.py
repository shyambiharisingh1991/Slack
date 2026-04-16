import os
import json
import logging
from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler
from flask import Flask, request
from dotenv import load_dotenv

# Import handlers
from handlers.events import register_events
from handlers.actions import register_actions
from handlers.views import register_views
from handlers.assessment_handlers import register_assessment_handlers

# Import storage functions
from db_storage import init_database, load_data_from_db, save_data_to_db

# Load environment variables
load_dotenv()

# Initialize logging
logging.basicConfig(level=logging.INFO)

# Initialize database
print("🔧 Initializing database...")
init_database()

# Global storage that persists to database
_app_data = None

def get_app_data(force_reload=False):
    """Get or initialize app data from database (always reloads to ensure fresh data)"""
    global _app_data
    
    # Always reload from database to ensure data is fresh
    # This prevents "assignment not found" errors after saving
    _app_data = load_data_from_db()
    if _app_data is None:
        # Fallback to default data
        from storage import load_data
        _app_data = load_data()
    
    return _app_data

def save_data(data):
    """Save data to database and update cache"""
    global _app_data
    _app_data = data
    save_data_to_db(data)

# Initialize app data
app_data = get_app_data()

# Initialize Flask app for Heroku (always, so the app boots)
flask_app = Flask(__name__)

# Only create Slack app when tokens are set (avoids BoltError at startup)
_slack_handler = None
if os.environ.get("SLACK_BOT_TOKEN") and os.environ.get("SLACK_SIGNING_SECRET"):
    app = App(
        token=os.environ.get("SLACK_BOT_TOKEN"),
        signing_secret=os.environ.get("SLACK_SIGNING_SECRET")
    )
    _slack_handler = SlackRequestHandler(app)
    register_events(app, get_app_data)
    register_actions(app, get_app_data, save_data)
    register_views(app, get_app_data, save_data)
    register_assessment_handlers(app, get_app_data, save_data)
    print("✅ Slack app initialized")
else:
    print("⚠️  SLACK_BOT_TOKEN or SLACK_SIGNING_SECRET not set. Set Heroku Config Vars and restart.")


@flask_app.route("/slack/events", methods=["POST"])
def slack_events():
    if _slack_handler:
        return _slack_handler.handle(request)
    # Return 503 so Slack retries; body explains the issue
    return (
        "Slack credentials not configured. Set SLACK_BOT_TOKEN and SLACK_SIGNING_SECRET in Heroku Config Vars.",
        503,
        {"Content-Type": "text/plain"},
    )


@flask_app.route("/", methods=["GET"])
def health_check():
    if _slack_handler:
        return "Learning Management Slack App is running!"
    return "App is running. Set SLACK_BOT_TOKEN and SLACK_SIGNING_SECRET in Heroku Config Vars to enable Slack."

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    flask_app.run(host="0.0.0.0", port=port, debug=True)
