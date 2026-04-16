def create_configurations_view(user_id, app_data):
    """Create the configurations tab view"""
    
    # Open access to everyone for now
    
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "⚙️ Configurations"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "Manage your learning management system settings, modules, assessments, and notifications."
            }
        },
        {
            "type": "divider"
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "📚 *Module Management*"
            }
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "➕ Create New Module"
                    },
                    "style": "primary",
                    "action_id": "create_module_button"
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "✏️ Edit Existing Module"
                    },
                    "action_id": "edit_module_button"
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "📋 View All Modules"
                    },
                    "action_id": "view_modules_button"
                }
            ]
        },
        {
            "type": "divider"
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "📝 *Assessment Management*"
            }
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "➕ Create New Assessment"
                    },
                    "style": "primary",
                    "action_id": "create_assessment_button"
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "✏️ Edit Existing Assessment"
                    },
                    "action_id": "edit_assessment_button"
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "📋 View All Assessments"
                    },
                    "action_id": "view_assessments_button"
                }
            ]
        },
        {
            "type": "divider"
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "🔔 *Notification Settings*"
            }
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "📧 Weekly Digest Settings"
                    },
                    "action_id": "weekly_digest_settings"
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "⏰ Reminder Settings"
                    },
                    "action_id": "reminder_settings"
                }
            ]
        },
        {
            "type": "divider"
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "📊 *System Information*"
            }
        }
    ]
    
    # Add system stats
    total_engineers = len(app_data["engineers"])
    total_modules = len(app_data["modules"])
    total_assessments = len(app_data["assessments"])
    total_assignments = len(app_data["assignments"])
    
    blocks.append({
        "type": "context",
        "elements": [
            {
                "type": "mrkdwn",
                "text": f"👥 Engineers: {total_engineers} | 📚 Modules: {total_modules} | 📝 Assessments: {total_assessments} | 📋 Assignments: {total_assignments}"
            }
        ]
    })
    
    return {
        "type": "home",
        "blocks": blocks
    }
