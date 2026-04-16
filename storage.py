import json
import os
from datetime import datetime

DATA_FILE = "app_data.json"

def load_data():
    """Load data from file, or initialize with defaults. (DB is used by app.py via db_storage directly.)"""
    # File storage fallback (used when DATABASE_URL is missing or DB unavailable)
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                data = json.load(f)
                print(f"✅ Loaded data from file - Engineers: {len(data.get('engineers', {}))}, Assignments: {len(data.get('assignments', {}))}")
                return data
        except Exception as e:
            print(f"❌ Error loading data file: {e}")
    
    # Initialize with default data
    print("📝 Initializing new app data")
    return {
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

def save_data(data):
    """Save data to database or file (used by db_storage when DB unavailable)."""
    # Try database first
    try:
        from db_storage import save_data_to_db
        save_data_to_db(data)
        return
    except Exception as e:
        print(f"⚠️ Database save failed, using file storage: {e}")
    
    # Fallback to file storage
    try:
        with open(DATA_FILE, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"💾 Saved data to file - Engineers: {len(data.get('engineers', {}))}, Assignments: {len(data.get('assignments', {}))}")
    except Exception as e:
        print(f"❌ Error saving data: {e}")

