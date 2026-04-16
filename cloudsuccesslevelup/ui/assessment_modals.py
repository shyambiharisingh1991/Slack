def create_assessment_modal(assessment_data=None):
    """Create modal for creating/editing an assessment"""
    is_edit = assessment_data is not None
    
    return {
        "type": "modal",
        "callback_id": "assessment_modal",
        "title": {
            "type": "plain_text",
            "text": "✏️ Edit Assessment" if is_edit else "➕ Create Assessment"
        },
        "submit": {
            "type": "plain_text",
            "text": "Save Assessment"
        },
        "close": {
            "type": "plain_text",
            "text": "Cancel"
        },
        "private_metadata": str(assessment_data["id"]) if is_edit else "",
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"{'Edit' if is_edit else 'Create'} an assessment"
                }
            },
            {
                "type": "input",
                "block_id": "assessment_name",
                "element": {
                    "type": "plain_text_input",
                    "action_id": "name_input",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "Enter assessment name"
                    },
                    "initial_value": assessment_data.get("name", "") if is_edit else ""
                },
                "label": {
                    "type": "plain_text",
                    "text": "Assessment Name"
                }
            },
            {
                "type": "input",
                "block_id": "assessment_description",
                "element": {
                    "type": "plain_text_input",
                    "action_id": "description_input",
                    "multiline": True,
                    "placeholder": {
                        "type": "plain_text",
                        "text": "Enter assessment description"
                    },
                    "initial_value": assessment_data.get("description", "") if is_edit else ""
                },
                "label": {
                    "type": "plain_text",
                    "text": "Description"
                }
            },
            {
                "type": "input",
                "block_id": "assessment_skills",
                "element": {
                    "type": "plain_text_input",
                    "action_id": "skills_input",
                    "multiline": True,
                    "placeholder": {
                        "type": "plain_text",
                        "text": "Enter skills assessed (one per line)"
                    },
                    "initial_value": assessment_data.get("skills", "") if is_edit else ""
                },
                "label": {
                    "type": "plain_text",
                    "text": "Skills Assessed"
                }
            },
            {
                "type": "input",
                "block_id": "assessment_duration",
                "element": {
                    "type": "plain_text_input",
                    "action_id": "duration_input",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "Enter duration in minutes"
                    },
                    "initial_value": str(assessment_data.get("duration_minutes", "")) if is_edit else ""
                },
                "label": {
                    "type": "plain_text",
                    "text": "Duration (minutes)"
                }
            }
        ]
    }

def create_assessment_selection_modal(app_data, action="edit"):
    """Create modal for selecting an assessment to edit"""
    assessment_options = []
    for assessment_id, assessment_data in app_data["assessments"].items():
        assessment_options.append({
            "text": {
                "type": "plain_text",
                "text": f"{assessment_data.get('name', 'Unknown Assessment')}"
            },
            "value": str(assessment_id)
        })
    
    if not assessment_options:
        return {
            "type": "modal",
            "callback_id": "assessment_selection_modal",
            "title": {
                "type": "plain_text",
                "text": "No Assessments Found"
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
                        "text": "No assessments have been created yet. Please create an assessment first."
                    }
                }
            ]
        }
    
    return {
        "type": "modal",
        "callback_id": "assessment_selection_modal",
        "title": {
            "type": "plain_text",
            "text": f"{action.title()} Assessment"
        },
        "submit": {
            "type": "plain_text",
            "text": f"{action.title()} Assessment"
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
                    "text": f"Select an assessment to {action}:"
                },
                "accessory": {
                    "type": "static_select",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "Select an assessment"
                    },
                    "options": assessment_options,
                    "action_id": "assessment_select"
                },
                "block_id": "assessment_selection"
            }
        ]
    }

def create_assessments_list_modal(app_data):
    """Create modal showing all assessments"""
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "📝 All Assessments"
            }
        }
    ]
    
    if not app_data["assessments"]:
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "No assessments have been created yet."
            }
        })
    else:
        for assessment_id, assessment_data in app_data["assessments"].items():
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"📝 *{assessment_data.get('name', 'Unknown Assessment')}*\n"
                           f"📄 {assessment_data.get('description', 'No description')}\n"
                           f"⏱️ Duration: {assessment_data.get('duration_minutes', 0)} minutes\n"
                           f"🎯 Skills: {assessment_data.get('skills', 'None specified')}"
                }
            })
            blocks.append({
                "type": "divider"
            })
    
    return {
        "type": "modal",
        "callback_id": "assessments_list_modal",
        "title": {
            "type": "plain_text",
            "text": "All Assessments"
        },
        "close": {
            "type": "plain_text",
            "text": "Close"
        },
        "blocks": blocks
    }
