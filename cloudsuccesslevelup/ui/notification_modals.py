def create_weekly_digest_modal(app_data):
    """Create modal for weekly digest settings"""
    # Get current settings (default if not set)
    settings = app_data.get("notification_settings", {})
    weekly_digest = settings.get("weekly_digest", {
        "enabled": True,
        "day": "Monday",
        "time": "09:00",
        "channels": [],
        "include_stats": True,
        "include_assignments": True
    })
    
    return {
        "type": "modal",
        "callback_id": "weekly_digest_modal",
        "title": {
            "type": "plain_text",
            "text": "📧 Weekly Digest Settings"
        },
        "submit": {
            "type": "plain_text",
            "text": "Save Settings"
        },
        "close": {
            "type": "plain_text",
            "text": "Cancel"
        },
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Configure weekly digest notifications for learning progress and updates."
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Enable Weekly Digest"
                },
                "accessory": {
                    "type": "checkboxes",
                    "action_id": "enable_digest",
                    "options": [
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "Send weekly digest"
                            },
                            "value": "enabled"
                        }
                    ],
                    "initial_options": [{"text": {"type": "plain_text", "text": "Send weekly digest"}, "value": "enabled"}] if weekly_digest.get("enabled") else []
                },
                "block_id": "digest_enabled"
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Day of Week"
                },
                "accessory": {
                    "type": "static_select",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "Select day"
                    },
                    "options": [
                        {"text": {"type": "plain_text", "text": "Monday"}, "value": "Monday"},
                        {"text": {"type": "plain_text", "text": "Tuesday"}, "value": "Tuesday"},
                        {"text": {"type": "plain_text", "text": "Wednesday"}, "value": "Wednesday"},
                        {"text": {"type": "plain_text", "text": "Thursday"}, "value": "Thursday"},
                        {"text": {"type": "plain_text", "text": "Friday"}, "value": "Friday"}
                    ],
                    "initial_option": {"text": {"type": "plain_text", "text": weekly_digest.get("day", "Monday")}, "value": weekly_digest.get("day", "Monday")},
                    "action_id": "day_select"
                },
                "block_id": "digest_day"
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Time (24-hour format)"
                },
                "accessory": {
                    "type": "static_select",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "Select time"
                    },
                    "options": [
                        {"text": {"type": "plain_text", "text": "08:00"}, "value": "08:00"},
                        {"text": {"type": "plain_text", "text": "09:00"}, "value": "09:00"},
                        {"text": {"type": "plain_text", "text": "10:00"}, "value": "10:00"},
                        {"text": {"type": "plain_text", "text": "11:00"}, "value": "11:00"},
                        {"text": {"type": "plain_text", "text": "12:00"}, "value": "12:00"},
                        {"text": {"type": "plain_text", "text": "13:00"}, "value": "13:00"},
                        {"text": {"type": "plain_text", "text": "14:00"}, "value": "14:00"},
                        {"text": {"type": "plain_text", "text": "15:00"}, "value": "15:00"},
                        {"text": {"type": "plain_text", "text": "16:00"}, "value": "16:00"},
                        {"text": {"type": "plain_text", "text": "17:00"}, "value": "17:00"}
                    ],
                    "initial_option": {"text": {"type": "plain_text", "text": weekly_digest.get("time", "09:00")}, "value": weekly_digest.get("time", "09:00")},
                    "action_id": "time_select"
                },
                "block_id": "digest_time"
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Include in Digest"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Progress Statistics"
                },
                "accessory": {
                    "type": "checkboxes",
                    "action_id": "include_stats",
                    "options": [
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "Include completion statistics"
                            },
                            "value": "stats"
                        }
                    ],
                    "initial_options": [{"text": {"type": "plain_text", "text": "Include completion statistics"}, "value": "stats"}] if weekly_digest.get("include_stats") else []
                },
                "block_id": "include_stats"
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Assignment Updates"
                },
                "accessory": {
                    "type": "checkboxes",
                    "action_id": "include_assignments",
                    "options": [
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "Include new assignments"
                            },
                            "value": "assignments"
                        }
                    ],
                    "initial_options": [{"text": {"type": "plain_text", "text": "Include new assignments"}, "value": "assignments"}] if weekly_digest.get("include_assignments") else []
                },
                "block_id": "include_assignments"
            }
        ]
    }

def create_reminder_settings_modal(app_data):
    """Create modal for reminder settings"""
    # Get current settings (default if not set)
    settings = app_data.get("notification_settings", {})
    reminders = settings.get("reminders", {
        "assignment_due": True,
        "assignment_overdue": True,
        "module_unlocked": True,
        "assessment_due": True,
        "days_before_due": 1,
        "overdue_frequency": "daily"
    })
    
    return {
        "type": "modal",
        "callback_id": "reminder_settings_modal",
        "title": {
            "type": "plain_text",
            "text": "⏰ Reminder Settings"
        },
        "submit": {
            "type": "plain_text",
            "text": "Save Settings"
        },
        "close": {
            "type": "plain_text",
            "text": "Cancel"
        },
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Configure automatic reminders for assignments and assessments."
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Reminder Types"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Assignment Due Reminders"
                },
                "accessory": {
                    "type": "checkboxes",
                    "action_id": "assignment_due_reminders",
                    "options": [
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "Send reminders for due assignments"
                            },
                            "value": "enabled"
                        }
                    ],
                    "initial_options": [{"text": {"type": "plain_text", "text": "Send reminders for due assignments"}, "value": "enabled"}] if reminders.get("assignment_due") else []
                },
                "block_id": "assignment_due"
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Overdue Assignment Reminders"
                },
                "accessory": {
                    "type": "checkboxes",
                    "action_id": "overdue_reminders",
                    "options": [
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "Send reminders for overdue assignments"
                            },
                            "value": "enabled"
                        }
                    ],
                    "initial_options": [{"text": {"type": "plain_text", "text": "Send reminders for overdue assignments"}, "value": "enabled"}] if reminders.get("assignment_overdue") else []
                },
                "block_id": "assignment_overdue"
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Module Unlocked Notifications"
                },
                "accessory": {
                    "type": "checkboxes",
                    "action_id": "module_unlocked_notifications",
                    "options": [
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "Notify when modules are unlocked"
                            },
                            "value": "enabled"
                        }
                    ],
                    "initial_options": [{"text": {"type": "plain_text", "text": "Notify when modules are unlocked"}, "value": "enabled"}] if reminders.get("module_unlocked") else []
                },
                "block_id": "module_unlocked"
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Assessment Due Reminders"
                },
                "accessory": {
                    "type": "checkboxes",
                    "action_id": "assessment_due_reminders",
                    "options": [
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "Send reminders for due assessments"
                            },
                            "value": "enabled"
                        }
                    ],
                    "initial_options": [{"text": {"type": "plain_text", "text": "Send reminders for due assessments"}, "value": "enabled"}] if reminders.get("assessment_due") else []
                },
                "block_id": "assessment_due"
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Days Before Due"
                },
                "accessory": {
                    "type": "static_select",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "Select days"
                    },
                    "options": [
                        {"text": {"type": "plain_text", "text": "1 day before"}, "value": "1"},
                        {"text": {"type": "plain_text", "text": "2 days before"}, "value": "2"},
                        {"text": {"type": "plain_text", "text": "3 days before"}, "value": "3"},
                        {"text": {"type": "plain_text", "text": "1 week before"}, "value": "7"}
                    ],
                    "action_id": "days_before_select"
                },
                "block_id": "days_before_due"
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Overdue Reminder Frequency"
                },
                "accessory": {
                    "type": "static_select",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "Select frequency"
                    },
                    "options": [
                        {"text": {"type": "plain_text", "text": "Daily"}, "value": "daily"},
                        {"text": {"type": "plain_text", "text": "Every 2 days"}, "value": "2days"},
                        {"text": {"type": "plain_text", "text": "Weekly"}, "value": "weekly"}
                    ],
                    "action_id": "overdue_frequency_select"
                },
                "block_id": "overdue_frequency"
            }
        ]
    }
