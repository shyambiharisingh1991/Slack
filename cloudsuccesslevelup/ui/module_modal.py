def create_module_start_modal(module_name, module_description, due_date, assignment_id):
    """Create modal for starting a module with Google link and acknowledge checkbox"""
    
    return {
        "type": "modal",
        "callback_id": "module_start_modal",
        "title": {
            "type": "plain_text",
            "text": f"📚 {module_name}"
        },
        "submit": {
            "type": "plain_text",
            "text": "Mark as Complete"
        },
        "close": {
            "type": "plain_text",
            "text": "Cancel"
        },
        "private_metadata": str(assignment_id),
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"📚 {module_name}"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Description:* {module_description}\n*Due Date:* {due_date}"
                }
            },
            {
                "type": "divider"
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "📖 *Learning Resources*\n\n⚠️ *You must click the button below to access the learning materials before you can complete this module:*"
                },
                "accessory": {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "🌐 Open Learning Materials"
                    },
                    "url": "https://google.com",
                    "action_id": "open_learning_materials"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "⚠️ *Step 1: Access Learning Materials*\n\nClick the button below to confirm you have accessed the learning materials:"
                },
                "block_id": "materials_accessed_status",
                "accessory": {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "✅ I Have Accessed Learning Materials"
                    },
                    "action_id": f"materials_accessed_{assignment_id}",
                    "style": "primary"
                }
            },
            {
                "type": "divider"
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "After reviewing the materials, please acknowledge that you have completed the module:"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Acknowledge completion"
                },
                "accessory": {
                    "type": "checkboxes",
                    "action_id": "acknowledge_completion",
                    "options": [
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "I have reviewed the learning materials and completed this module"
                            },
                            "value": "acknowledged"
                        }
                    ]
                },
                "block_id": "acknowledge_checkbox"
            }
        ]
    }
