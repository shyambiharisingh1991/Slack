import os
import json
from urllib.parse import urlparse

def get_db_connection():
    """Get PostgreSQL database connection. Only imports psycopg2 when DATABASE_URL is set."""
    database_url = os.environ.get('DATABASE_URL')
    
    if not database_url:
        print("⚠️  No DATABASE_URL found, falling back to file storage")
        return None
    
    try:
        import psycopg2
        from psycopg2.extras import RealDictCursor
    except ImportError:
        print("⚠️  psycopg2 not installed (run: pip install psycopg2-binary). Falling back to file storage.")
        return None
    
    # Parse database URL
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    try:
        conn = psycopg2.connect(database_url, cursor_factory=RealDictCursor)
        return conn
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return None

def init_database():
    """Initialize database tables"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cur = conn.cursor()
        
        # Create app_data table to store JSON data
        cur.execute('''
            CREATE TABLE IF NOT EXISTS app_data (
                id INTEGER PRIMARY KEY DEFAULT 1,
                data JSONB NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Check if data exists
        cur.execute('SELECT COUNT(*) as count FROM app_data')
        count = cur.fetchone()['count']
        
        if count == 0:
            # Initialize with default data
            default_data = {
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
            
            cur.execute(
                'INSERT INTO app_data (id, data) VALUES (1, %s)',
                (json.dumps(default_data),)
            )
            print("✅ Database initialized with default data")
        else:
            print("✅ Database already initialized")
        
        conn.commit()
        cur.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database initialization error: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return False

def load_data_from_db():
    """Load data from PostgreSQL database"""
    conn = get_db_connection()
    if not conn:
        # Fallback to file storage
        from storage import load_data as load_from_file
        return load_from_file()
    
    try:
        cur = conn.cursor()
        cur.execute('SELECT data FROM app_data WHERE id = 1')
        result = cur.fetchone()
        
        if result:
            data = result['data']
            print(f"📊 Loaded from database - Engineers: {len(data.get('engineers', {}))}, Assignments: {len(data.get('assignments', {}))}")
            cur.close()
            conn.close()
            return data
        else:
            print("⚠️  No data found in database")
            cur.close()
            conn.close()
            return None
            
    except Exception as e:
        print(f"❌ Error loading from database: {e}")
        if conn:
            conn.close()
        # Fallback to file storage
        from storage import load_data as load_from_file
        return load_from_file()

def save_data_to_db(data):
    """Save data to PostgreSQL database"""
    conn = get_db_connection()
    if not conn:
        # Fallback to file storage
        from storage import save_data as save_to_file
        save_to_file(data)
        return
    
    try:
        cur = conn.cursor()
        cur.execute(
            '''UPDATE app_data 
               SET data = %s, updated_at = CURRENT_TIMESTAMP 
               WHERE id = 1''',
            (json.dumps(data),)
        )
        conn.commit()
        print(f"💾 Saved to database - Engineers: {len(data.get('engineers', {}))}, Assignments: {len(data.get('assignments', {}))}")
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error saving to database: {e}")
        if conn:
            conn.rollback()
            conn.close()
        # Fallback to file storage
        from storage import save_data as save_to_file
        save_to_file(data)
