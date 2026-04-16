def register_events(app, get_app_data):
    """Register all event handlers"""
    
    @app.event("app_home_opened")
    def update_home_tab(client, event, logger):
        try:
            # Get user info
            user_id = event["user"]
            
            # Get current app data
            app_data = get_app_data()
            
            # Create home view
            from ui.home import create_home_view
            view = create_home_view(user_id, app_data)
            
            # Update the home tab
            client.views_publish(
                user_id=user_id,
                view=view
            )
            
        except Exception as e:
            logger.error(f"Error publishing home tab: {e}")
