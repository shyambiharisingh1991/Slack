import json

def create_engineer_modal():
    """Create modal for adding a new engineer"""
    return {
        "type": "modal",
        "callback_id": "add_engineer_modal",
        "title": {
            "type": "plain_text",
            "text": "Add New Engineer"
        },
        "submit": {
            "type": "plain_text",
            "text": "Add Engineer"
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
                    "text": "Select the engineer to add to the system:"
                },
                "accessory": {
                    "type": "users_select",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "Select an engineer"
                    },
                    "action_id": "slack_user_select"
                },
                "block_id": "engineer_slack_user"
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Select the team:"
                },
                "accessory": {
                    "type": "static_select",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "Select a team"
                    },
                    "options": [
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "Support"
                            },
                            "value": "support"
                        },
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "Guides"
                            },
                            "value": "guides"
                        },
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "Success Architects"
                            },
                            "value": "success_architects"
                        },
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "FDE"
                            },
                            "value": "fde"
                        }
                    ],
                    "action_id": "team_select"
                },
                "block_id": "engineer_team"
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Select the geo:"
                },
                "accessory": {
                    "type": "static_select",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "Select a geo"
                    },
                    "options": [
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "Americas"
                            },
                            "value": "americas"
                        },
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "EMEA"
                            },
                            "value": "emea"
                        },
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "APAC"
                            },
                            "value": "apac"
                        }
                    ],
                    "action_id": "geo_select"
                },
                "block_id": "engineer_geo"
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Select the onboarding plan:"
                },
                "accessory": {
                    "type": "static_select",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "Select a plan"
                    },
                    "options": [
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "Sales Signature"
                            },
                            "value": "sales_signature"
                        },
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "Service - Signature"
                            },
                            "value": "service_signature"
                        },
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "Service Premier"
                            },
                            "value": "service_premier"
                        },
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "ProM"
                            },
                            "value": "prom"
                        },
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "Guides"
                            },
                            "value": "guides"
                        },
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "Success Architect"
                            },
                            "value": "success_architect"
                        }
                    ],
                    "action_id": "plan_select"
                },
                "block_id": "onboarding_plan"
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Select the start date:"
                },
                "accessory": {
                    "type": "datepicker",
                    "initial_date": "2025-09-20",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "Select a date"
                    },
                    "action_id": "start_date_picker"
                },
                "block_id": "start_date"
            }
        ]
    }

def create_assign_module_modal(app_data):
    """Create modal for assigning a module"""
    # Predefined modules list
    predefined_modules = [
        {"name": "Agentforce", "duration": 3, "description": "Learn Salesforce Agentforce platform"},
        {"name": "Data Cloud", "duration": 5, "description": "Master Salesforce Data Cloud capabilities"},
        {"name": "Apex", "duration": 7, "description": "Develop with Salesforce Apex programming"},
        {"name": "Integration", "duration": 4, "description": "Build integrations with Salesforce APIs"},
        {"name": "Message Queue", "duration": 3, "description": "Implement message queuing solutions"},
        {"name": "Deployments", "duration": 2, "description": "Deploy applications using CI/CD"}
    ]
    
    module_options = []
    for i, module in enumerate(predefined_modules):
        module_options.append({
            "text": {
                "type": "plain_text",
                "text": f"{module['name']} ({module['duration']} days)"
            },
            "value": f"predefined_{i}"
        })
    
    return {
        "type": "modal",
        "callback_id": "assign_module_modal",
        "title": {
            "type": "plain_text",
            "text": "Assign Module"
        },
        "submit": {
            "type": "plain_text",
            "text": "Assign Module"
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
                    "text": "Select the user:"
                },
                "accessory": {
                    "type": "users_select",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "Select a user"
                    },
                    "action_id": "engineer_select"
                },
                "block_id": "engineer_selection"
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Select the module:"
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
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Select the due date (cannot be in the past):"
                },
                "accessory": {
                    "type": "datepicker",
                    "initial_date": "2025-01-15",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "Select a date"
                    },
                    "action_id": "due_date_picker"
                },
                "block_id": "due_date"
            }
        ]
    }

def create_assign_assessment_modal(app_data):
    """Create modal for assigning an assessment"""
    # Get available assessments from app_data
    assessment_options = []
    for assessment_id, assessment_data in app_data.get("assessments", {}).items():
        assessment_options.append({
            "text": {
                "type": "plain_text",
                "text": f"{assessment_data.get('name', 'Unknown Assessment')} ({assessment_data.get('duration_minutes', 0)} min)"
            },
            "value": str(assessment_id)
        })
    
    # If no assessments available, show a message
    if not assessment_options:
        return {
            "type": "modal",
            "callback_id": "assign_assessment_modal",
            "title": {
                "type": "plain_text",
                "text": "No Assessments Available"
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
                        "text": "No assessments have been created yet. Please create assessments first in the Configurations tab."
                    }
                }
            ]
        }
    
    return {
        "type": "modal",
        "callback_id": "assign_assessment_modal",
        "title": {
            "type": "plain_text",
            "text": "Assign Assessment"
        },
        "submit": {
            "type": "plain_text",
            "text": "Assign Assessment"
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
                    "text": "Select the user:"
                },
                "accessory": {
                    "type": "users_select",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "Select a user"
                    },
                    "action_id": "engineer_select"
                },
                "block_id": "engineer_selection"
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Select the assessment:"
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
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Select the due date:"
                },
                "accessory": {
                    "type": "datepicker",
                    "initial_date": "2025-09-27",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "Select a date"
                    },
                    "action_id": "due_date_picker"
                },
                "block_id": "due_date"
            }
        ]
    }

def create_detailed_report_modal(app_data):
    """Create modal for detailed reports"""
    return {
        "type": "modal",
        "callback_id": "detailed_report_modal",
        "title": {
            "type": "plain_text",
            "text": "📊 Detailed Report"
        },
        "close": {
            "type": "plain_text",
            "text": "Close"
        },
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "📊 Detailed Report"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Select a report type to view detailed analytics:"
                }
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "View by Engineer"
                        },
                        "action_id": "report_by_engineer",
                        "style": "primary"
                    }
                ]
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "View by Module"
                        },
                        "action_id": "report_by_module"
                    }
                ]
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "View by Assessment Skills"
                        },
                        "action_id": "report_by_assessment"
                    }
                ]
            }
        ]
    }

def create_progress_update_modal(assignment_id, module_name):
    """Create modal for updating progress"""
    return {
        "type": "modal",
        "callback_id": "progress_update_modal",
        "title": {
            "type": "plain_text",
            "text": "Update Progress"
        },
        "submit": {
            "type": "plain_text",
            "text": "Update Progress"
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
                    "text": f"Update progress for *{module_name}*:"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Progress Percentage:"
                },
                "accessory": {
                    "type": "static_select",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "Select progress"
                    },
                    "options": [
                        {"text": {"type": "plain_text", "text": "0% - Not Started"}, "value": "0"},
                        {"text": {"type": "plain_text", "text": "25% - Getting Started"}, "value": "25"},
                        {"text": {"type": "plain_text", "text": "50% - Halfway Done"}, "value": "50"},
                        {"text": {"type": "plain_text", "text": "75% - Almost There"}, "value": "75"},
                        {"text": {"type": "plain_text", "text": "100% - Completed"}, "value": "100"}
                    ],
                    "action_id": "progress_select"
                },
                "block_id": "progress_percentage"
            },
            {
                "type": "input",
                "block_id": "notes",
                "element": {
                    "type": "plain_text_input",
                    "action_id": "notes_input",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "Add any notes about your progress..."
                    },
                    "multiline": True
                },
                "label": {
                    "type": "plain_text",
                    "text": "Notes (Optional)"
                },
                "optional": True
            }
        ],
        "private_metadata": assignment_id
    }

def create_engineer_selection_modal(app_data):
    """Create modal for selecting an engineer to view detailed report"""
    # Get all engineers from app_data
    engineer_options = []
    for engineer_id, engineer_data in app_data["engineers"].items():
        engineer_options.append({
            "text": {
                "type": "plain_text",
                "text": f"{engineer_data.get('name', 'Unknown Engineer')} ({engineer_data.get('team', 'No Team')})"
            },
            "value": str(engineer_id)
        })
    
    # If no engineers in app_data, show a message to add engineers first
    if not engineer_options:
        return {
            "type": "modal",
            "callback_id": "engineer_selection_modal",
            "title": {
                "type": "plain_text",
                "text": "No Engineers Found"
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
                        "text": "No engineers have been added yet. Please add engineers first using the 'Add New Engineer' button on the Home tab."
                    }
                }
            ]
        }
    
    return {
        "type": "modal",
        "callback_id": "engineer_selection_modal",
        "title": {
            "type": "plain_text",
            "text": "Select Engineer"
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
                    "text": "Select an engineer to view their detailed report:"
                },
                "accessory": {
                    "type": "static_select",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "Select an engineer"
                    },
                    "options": engineer_options,
                    "action_id": "selected_engineer"
                }
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "View Report"
                        },
                        "style": "primary",
                        "action_id": "view_engineer_report"
                    }
                ]
            }
        ]
    }

def create_module_selection_modal(app_data):
    """Create modal for selecting a module to view detailed report"""
    # Get all modules from app_data
    module_options = []
    for module_id, module_data in app_data["modules"].items():
        module_options.append({
            "text": {
                "type": "plain_text",
                "text": module_data.get("name", "Unknown Module")
            },
            "value": str(module_id)
        })
    
    # If no modules in app_data, show a message
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
                        "text": "No modules have been created yet. Modules will be created when engineers are added."
                    }
                }
            ]
        }
    
    return {
        "type": "modal",
        "callback_id": "module_selection_modal",
        "title": {
            "type": "plain_text",
            "text": "Select Module"
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
                    "text": "Select a module to view detailed report:"
                },
                "accessory": {
                    "type": "static_select",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "Select a module"
                    },
                    "options": module_options,
                    "action_id": "selected_module"
                }
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "View Report"
                        },
                        "style": "primary",
                        "action_id": "view_module_report"
                    }
                ]
            }
        ]
    }

def create_assessment_selection_modal(app_data):
    """Create modal for selecting an assessment to view detailed report"""
    # Get all assessments from app_data
    assessment_options = []
    for assessment_id, assessment_data in app_data["assessments"].items():
        assessment_options.append({
            "text": {
                "type": "plain_text",
                "text": assessment_data.get("name", "Unknown Assessment")
            },
            "value": str(assessment_id)
        })
    
    # If no assessments in app_data, show a message
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
                        "text": "No assessments have been created yet. Assessments will be created when they are assigned to engineers."
                    }
                }
            ]
        }
    
    return {
        "type": "modal",
        "callback_id": "assessment_selection_modal",
        "title": {
            "type": "plain_text",
            "text": "Select Assessment"
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
                    "text": "Select an assessment to view detailed report:"
                },
                "accessory": {
                    "type": "static_select",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "Select an assessment"
                    },
                    "options": assessment_options,
                    "action_id": "selected_assessment"
                }
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "View Report"
                        },
                        "style": "primary",
                        "action_id": "view_assessment_report"
                    }
                ]
            }
        ]
    }
