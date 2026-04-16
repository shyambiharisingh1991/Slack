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

# Load environment variables
load_dotenv()

# Initialize logging
logging.basicConfig(level=logging.INFO)

# Global in-memory storage that persists across requests
_app_data = None

def get_app_data():
    """Get or initialize app data"""
    global _app_data
    if _app_data is None:
        _app_data = {
            "engineers": {},
            "modules": {
                "1": {
                    "id": 1,
                    "name": "Python Fundamentals",
                    "description": "Learn the basics of Python programming including variables, data types, and control structures.",
                    "duration_days": 5,
                    "skills": "Python, Variables, Data Types, Control Structures",
                    "created_at": "2025-01-01T00:00:00"
                },
                "2": {
                    "id": 2,
                    "name": "Web Development Basics",
                    "description": "Introduction to HTML, CSS, and JavaScript for web development.",
                    "duration_days": 7,
                    "skills": "HTML, CSS, JavaScript, Web Development",
                    "created_at": "2025-01-01T00:00:00"
                }
            },
            "assignments": {},
            "assessments": {
                "1": {
                    "id": 1,
                    "name": "Python Quiz",
                    "description": "Test your knowledge of Python fundamentals",
                    "duration_minutes": 30,
                    "questions": 10,
                    "passing_score": 70,
                    "created_at": "2025-01-01T00:00:00"
                },
                "2": {
                    "id": 2,
                    "name": "Web Development Assessment",
                    "description": "Practical assessment of web development skills",
                    "duration_minutes": 60,
                    "questions": 15,
                    "passing_score": 80,
                    "created_at": "2025-01-01T00:00:00"
                }
            },
            "progress": {},
            "next_ids": {"engineers": 1, "modules": 3, "assignments": 1, "assessments": 3, "progress": 1}
        }
        print("Initialized new app data in memory with sample modules and assessments")
    return _app_data

def save_data(data):
    """Save data to memory (no-op since data is already in memory)"""
    global _app_data
    _app_data = data
    print(f"Data saved to memory - Engineers: {len(data['engineers'])}, Assignments: {len(data['assignments'])}")

# Initialize app data
app_data = get_app_data()

# Initialize Slack app
app = App(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET")
)

# Initialize Flask app for Heroku
flask_app = Flask(__name__)
handler = SlackRequestHandler(app)

# Register all handlers with data access functions
register_events(app, get_app_data)
register_actions(app, get_app_data, save_data)
register_views(app, get_app_data, save_data)


@flask_app.route("/slack/events", methods=["POST"])
def slack_events():
    return handler.handle(request)

@flask_app.route("/", methods=["GET"])
def health_check():
    return "Learning Management Slack App is running!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    flask_app.run(host="0.0.0.0", port=port, debug=True)
