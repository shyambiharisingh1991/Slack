def create_module_modal(module_data=None):
    """Create modal for creating/editing a module"""
    is_edit = module_data is not None
    
    return {
        "type": "modal",
        "callback_id": "module_modal",
        "title": {
            "type": "plain_text",
            "text": "✏️ Edit Module" if is_edit else "➕ Create Module"
        },
        "submit": {
            "type": "plain_text",
            "text": "Save Module"
        },
        "close": {
            "type": "plain_text",
            "text": "Cancel"
        },
        "private_metadata": str(module_data["id"]) if is_edit else "",
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"{'Edit' if is_edit else 'Create'} a learning module"
                }
            },
            {
                "type": "input",
                "block_id": "module_name",
                "element": {
                    "type": "plain_text_input",
                    "action_id": "name_input",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "Enter module name"
                    },
                    "initial_value": module_data.get("name", "") if is_edit else ""
                },
                "label": {
                    "type": "plain_text",
                    "text": "Module Name"
                }
            },
            {
                "type": "input",
                "block_id": "module_description",
                "element": {
                    "type": "plain_text_input",
                    "action_id": "description_input",
                    "multiline": True,
                    "placeholder": {
                        "type": "plain_text",
                        "text": "Enter module description"
                    },
                    "initial_value": module_data.get("description", "") if is_edit else ""
                },
                "label": {
                    "type": "plain_text",
                    "text": "Description"
                }
            },
            {
                "type": "input",
                "block_id": "module_duration",
                "element": {
                    "type": "plain_text_input",
                    "action_id": "duration_input",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "Enter duration in days"
                    },
                    "initial_value": str(module_data.get("duration_days", "")) if is_edit else ""
                },
                "label": {
                    "type": "plain_text",
                    "text": "Duration (days)"
                }
            },
            {
                "type": "input",
                "block_id": "module_skills",
                "element": {
                    "type": "plain_text_input",
                    "action_id": "skills_input",
                    "multiline": True,
                    "placeholder": {
                        "type": "plain_text",
                        "text": "Enter skills covered (one per line)"
                    },
                    "initial_value": module_data.get("skills", "") if is_edit else ""
                },
                "label": {
                    "type": "plain_text",
                    "text": "Skills Covered"
                }
            }
        ]
    }

def create_module_selection_modal(app_data, action="edit"):
    """Create modal for selecting a module to edit"""
    module_options = []
    for module_id, module_data in app_data["modules"].items():
        module_options.append({
            "text": {
                "type": "plain_text",
                "text": f"{module_data.get('name', 'Unknown Module')} ({module_data.get('duration_days', 0)} days)"
            },
            "value": str(module_id)
        })
    
    if not module_options:
        return {
            "type": "modal",
            "callback_id": "module_selection_modal",
            "title": {
                "type": "plain_text",
                "text": "No Modules Found"
            },
            "close": {
                "type": "plain_text",
                "text": "Close"
            },
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "No modules have been created yet. Please create a module first."
                    }
                }
            ]
        }
    
    return {
        "type": "modal",
        "callback_id": "module_selection_modal",
        "title": {
            "type": "plain_text",
            "text": f"{action.title()} Module"
        },
        "submit": {
            "type": "plain_text",
            "text": f"{action.title()} Module"
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
                    "text": f"Select a module to {action}:"
                },
                "accessory": {
                    "type": "static_select",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "Select a module"
                    },
                    "options": module_options,
                    "action_id": "module_select"
                },
                "block_id": "module_selection"
            }
        ]
    }

def create_modules_list_modal(app_data):
    """Create modal showing all modules"""
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "📚 All Modules"
            }
        }
    ]
    
    if not app_data["modules"]:
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "No modules have been created yet."
            }
        })
    else:
        for module_id, module_data in app_data["modules"].items():
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"📚 *{module_data.get('name', 'Unknown Module')}*\n"
                           f"📝 {module_data.get('description', 'No description')}\n"
                           f"⏱️ Duration: {module_data.get('duration_days', 0)} days\n"
                           f"🎯 Skills: {module_data.get('skills', 'None specified')}"
                }
            })
            blocks.append({
                "type": "divider"
            })
    
    return {
        "type": "modal",
        "callback_id": "modules_list_modal",
        "title": {
            "type": "plain_text",
            "text": "All Modules"
        },
        "close": {
            "type": "plain_text",
            "text": "Close"
        },
        "blocks": blocks
    }
