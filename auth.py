"""
Authorization and access control helpers
"""
import os

def get_admin_user_ids():
    """Get list of admin user IDs from environment variable"""
    admin_ids = os.getenv('ADMIN_USER_IDS', '')
    if admin_ids:
        return [uid.strip() for uid in admin_ids.split(',') if uid.strip()]
    return []

def is_admin(user_id, app_data=None):
    """
    Check if a user is an admin/manager
    
    Checks:
    1. Environment variable ADMIN_USER_IDS
    2. Database role field (if app_data provided)
    """
    # Check environment variable
    if user_id in get_admin_user_ids():
        return True
    
    # Check database role
    if app_data:
        for eng_id, eng_data in app_data.get("engineers", {}).items():
            if eng_data.get("slack_user_id") == user_id:
                # Check if user has admin/manager role
                role = eng_data.get("role", "engineer")
                if role in ["admin", "manager"]:
                    return True
    
    return False

def get_user_role(user_id, app_data):
    """Get the role of a user"""
    # Check if admin from environment
    if user_id in get_admin_user_ids():
        return "admin"
    
    # Check database
    if app_data:
        for eng_id, eng_data in app_data.get("engineers", {}).items():
            if eng_data.get("slack_user_id") == user_id:
                return eng_data.get("role", "engineer")
    
    # Default to engineer for users in system, unknown for others
    return "engineer"

def require_admin(func):
    """Decorator to require admin access for a handler"""
    def wrapper(ack, body, client, *args, **kwargs):
        user_id = body["user"]["id"]
        
        # Import here to avoid circular dependency
        from app import get_app_data
        app_data = get_app_data()
        
        if not is_admin(user_id, app_data):
            ack()
            client.chat_postMessage(
                channel=user_id,
                text="❌ *Access Denied*\n\nYou don't have permission to perform this action. This feature is restricted to managers and administrators only."
            )
            return
        
        # User is admin, proceed
        return func(ack, body, client, *args, **kwargs)
    
    return wrapper

