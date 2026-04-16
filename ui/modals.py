import json
from datetime import date
from engineer_tenures import get_team, get_all_tenures

def create_engineer_modal():
    """Create modal for adding a new engineer"""
    from datetime import date
    
    # Set initial date to today
    today = date.today().strftime("%Y-%m-%d")
    
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
                                "text": "APAC"
                            },
                            "value": "apac"
                        },
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "IST"
                            },
                            "value": "ist"
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
                                "text": "AMER EST"
                            },
                            "value": "amer_est"
                        },
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "AMER PST"
                            },
                            "value": "amer_pst"
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
                    "initial_date": today,
                    "placeholder": {
                        "type": "plain_text",
                        "text": "Select a date"
                    },
                    "action_id": "start_date_picker"
                },
                "block_id": "start_date"
            },
            {
                "type": "input",
                "block_id": "trailhead_username",
                "optional": True,
                "element": {
                    "type": "plain_text_input",
                    "action_id": "trailhead_input",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "e.g. shyam-bihari"
                    }
                },
                "label": {
                    "type": "plain_text",
                    "text": "Trailhead Username (optional)"
                },
                "hint": {
                    "type": "plain_text",
                    "text": "From trailblazer.me/id/<username>. Used to link their Trailhead profile."
                }
            }
        ]
    }

def create_assign_module_modal(app_data):
    """Create modal for assigning a module"""
    from datetime import date, timedelta
    
    # Set initial date to tomorrow to prevent past date selection
    tomorrow = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")
    
    # Predefined modules list
    predefined_modules = [
        {"name": "Agentforce", "duration": 3, "description": "Learn Salesforce Agentforce platform"},
        {"name": "Data Cloud", "duration": 5, "description": "Master Salesforce Data Cloud capabilities"},
        {"name": "Apex", "duration": 7, "description": "Develop with Salesforce Apex programming"},
        {"name": "Integration", "duration": 4, "description": "Build integrations with Salesforce APIs"},
        {"name": "Message Queue", "duration": 3, "description": "Implement message queuing solutions"},
        {"name": "Deployments", "duration": 2, "description": "Deploy applications using CI/CD"},
        {"name": "March Accreditation", "duration": 0, "description": "Watch the video and review upcoming changes in March. Acknowledge to complete."},
    ]
    
    module_options = []
    for i, module in enumerate(predefined_modules):
        duration = module.get("duration", 0)
        label = f"{module['name']} ({duration} days)" if duration else module["name"]
        module_options.append({
            "text": {"type": "plain_text", "text": label},
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
                    "text": "*Select the due date:*\n⚠️ _Due date must be today or in the future_"
                },
                "accessory": {
                    "type": "datepicker",
                    "initial_date": tomorrow,
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
    from datetime import date, timedelta
    
    # Set initial date to tomorrow to prevent past date selection
    tomorrow = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")
    
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
                    "text": "*Select the due date:*\n⚠️ _Due date must be today or in the future_"
                },
                "accessory": {
                    "type": "datepicker",
                    "initial_date": tomorrow,
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

def create_report_type_selection_modal():
    """Create initial modal to select report type"""
    return {
        "type": "modal",
        "callback_id": "report_type_selection_modal",
        "title": {
            "type": "plain_text",
            "text": "📊 Select Report"
        },
        "close": {
            "type": "plain_text",
            "text": "Cancel"
        },
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "📊 Generate Detailed Report"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*Select the type of report* you want to generate:"
                }
            },
            {
                "type": "divider"
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "👤 By Engineer"
                        },
                        "style": "primary",
                        "action_id": "report_type_by_engineer"
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "📚 By Module"
                        },
                        "style": "primary",
                        "action_id": "report_type_by_module"
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
                            "text": "📋 By Assessments"
                        },
                        "style": "primary",
                        "action_id": "report_type_by_assessments"
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "⏰ Due Report"
                        },
                        "action_id": "report_type_due_report"
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
                    "text": "📄 *Report Types:*\n• *By Engineer:* Complete training report for a specific engineer\n• *By Module:* All engineers assigned to a specific module\n• *By Assessments:* All engineers assigned to specific assessments\n• *Due Report:* Engineers who are behind schedule on their assignments"
                }
            }
        ]
    }

def create_engineer_report_modal(app_data):
    """Create modal for engineer report with only engineer selection"""
    
    # Get list of engineers for selection
    engineer_options = []
    for eng_id, eng_data in app_data.get("engineers", {}).items():
        engineer_options.append({
            "text": {
                "type": "plain_text",
                "text": eng_data.get("name", "Unknown Engineer")
            },
            "value": str(eng_id)
        })
    
    if not engineer_options:
        engineer_options.append({
            "text": {
                "type": "plain_text",
                "text": "No engineers available"
            },
            "value": "none"
        })
    
    return {
        "type": "modal",
        "callback_id": "engineer_report_modal",
        "title": {
            "type": "plain_text",
            "text": "👤 Engineer Report"
        },
        "submit": {
            "type": "plain_text",
            "text": "Generate PDF"
        },
        "close": {
            "type": "plain_text",
            "text": "Cancel"
        },
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "👤 Engineer Training Report"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Generate a comprehensive training report for a specific engineer."
                }
            },
            {
                "type": "divider"
            },
            {
                "type": "input",
                "block_id": "engineer_selection",
                "element": {
                    "type": "static_select",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "Select an engineer"
                    },
                    "options": engineer_options,
                    "action_id": "selected_engineer"
                },
                "label": {
                    "type": "plain_text",
                    "text": "Engineer"
                }
            }
        ]
    }


def create_talent_profile_modal(app_data):
    """Create modal to select an engineer and view their Talent Profile (LinkedIn-style for leaders/recruiters)."""
    engineer_options = []
    for eng_id, eng_data in app_data.get("engineers", {}).items():
        name = eng_data.get("name", "Unknown")
        team = get_team(eng_data).replace("_", " ").title()
        engineer_options.append({
            "text": {"type": "plain_text", "text": f"{name} · {team}"},
            "value": str(eng_id)
        })
    if not engineer_options:
        engineer_options = [{"text": {"type": "plain_text", "text": "No engineers available"}, "value": "none"}]
    return {
        "type": "modal",
        "callback_id": "talent_profile_modal",
        "title": {"type": "plain_text", "text": "Talent Profile"},
        "submit": {"type": "plain_text", "text": "View Profile"},
        "close": {"type": "plain_text", "text": "Cancel"},
        "blocks": [
            {"type": "header", "text": {"type": "plain_text", "text": "👤 Talent Profile", "emoji": True}},
            {"type": "section", "text": {"type": "mrkdwn", "text": "Select an engineer to view their profile — role history, learning progress, and skills. Great for leaders and internal recruiters."}},
            {"type": "divider"},
            {
                "type": "input",
                "block_id": "talent_engineer_selection",
                "element": {
                    "type": "static_select",
                    "placeholder": {"type": "plain_text", "text": "Select engineer"},
                    "options": engineer_options,
                    "action_id": "selected_engineer"
                },
                "label": {"type": "plain_text", "text": "Engineer"}
            }
        ]
    }


def create_set_end_date_modal(app_data, initial_engineer_id=None):
    """Create modal to set end date for an engineer's current/ongoing tenure (engineer profile option)."""
    options = []
    initial_option = None
    for eng_id, eng_data in app_data.get("engineers", {}).items():
        tenures = get_all_tenures(eng_data)
        name = eng_data.get("name", "Unknown")
        for idx, t in enumerate(tenures):
            if t.get("end_date") is not None:
                continue
            team = t.get("team", "unassigned").replace("_", " ").title()
            geo = (t.get("geo") or "unassigned").upper() if len(str(t.get("geo", ""))) <= 4 else str(t.get("geo", "unassigned")).title()
            start = (t.get("start_date") or "")[:10] or "—"
            opt_value = f"{eng_id}|{idx}"
            opt = {
                "text": {"type": "plain_text", "text": f"{name} – {team} ({geo}) – started {start}"},
                "value": opt_value,
            }
            options.append(opt)
            if initial_engineer_id and str(eng_id) == str(initial_engineer_id) and initial_option is None:
                initial_option = opt
    if not options:
        options = [{"text": {"type": "plain_text", "text": "No ongoing tenures"}, "value": "none"}]
    today = date.today().strftime("%Y-%m-%d")
    block_tenure = {
        "type": "input",
        "block_id": "tenure_selection",
        "element": {
            "type": "static_select",
            "placeholder": {"type": "plain_text", "text": "Select tenure to end"},
            "options": options,
            "action_id": "tenure_select",
        },
        "label": {"type": "plain_text", "text": "Engineer & tenure (ongoing)"},
    }
    if initial_option and initial_option["value"] != "none":
        block_tenure["element"]["initial_option"] = initial_option
    return {
        "type": "modal",
        "callback_id": "set_end_date_modal",
        "title": {"type": "plain_text", "text": "Set end date"},
        "submit": {"type": "plain_text", "text": "Set end date"},
        "close": {"type": "plain_text", "text": "Cancel"},
        "blocks": [
            {"type": "section", "text": {"type": "mrkdwn", "text": "Set an end date for an ongoing team tenure. This will mark that stint as ended (PDF and Home will show it correctly)."}},
            {"type": "divider"},
            block_tenure,
            {
                "type": "input",
                "block_id": "end_date_block",
                "element": {
                    "type": "datepicker",
                    "initial_date": today,
                    "placeholder": {"type": "plain_text", "text": "Select end date"},
                    "action_id": "end_date_picker",
                },
                "label": {"type": "plain_text", "text": "End date"},
            },
        ],
    }


def create_module_report_modal(app_data):
    """Create modal for module report with only module selection"""
    
    # Get list of modules
    module_options = []
    # Add predefined modules
    predefined_modules = {
        "0": "Agentforce",
        "1": "Data Cloud",
        "2": "Apex",
        "3": "Integration",
        "4": "Message Queue",
        "5": "Deployments"
    }
    for mod_id, mod_name in predefined_modules.items():
        module_options.append({
            "text": {
                "type": "plain_text",
                "text": mod_name
            },
            "value": f"predefined_{mod_id}"
        })
    
    # Add custom modules
    for mod_id, mod_data in app_data.get("modules", {}).items():
        module_options.append({
            "text": {
                "type": "plain_text",
                "text": mod_data.get("name", "Unknown Module")
            },
            "value": str(mod_id)
        })
    
    if not module_options:
        module_options.append({
            "text": {
                "type": "plain_text",
                "text": "No modules available"
            },
            "value": "none"
        })
    
    return {
        "type": "modal",
        "callback_id": "module_report_modal",
        "title": {
            "type": "plain_text",
            "text": "📚 Module Report"
        },
        "submit": {
            "type": "plain_text",
            "text": "Generate PDF"
        },
        "close": {
            "type": "plain_text",
            "text": "Cancel"
        },
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "📚 Module Assignment Report"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Generate a report showing all engineers assigned to a specific module."
                }
            },
            {
                "type": "divider"
            },
            {
                "type": "input",
                "block_id": "module_selection",
                "element": {
                    "type": "static_select",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "Select a module"
                    },
                    "options": module_options,
                    "action_id": "selected_module"
                },
                "label": {
                    "type": "plain_text",
                    "text": "Module"
                }
            },
            {
                "type": "input",
                "block_id": "status_filter",
                "optional": True,
                "element": {
                    "type": "static_select",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "Filter by status (optional)"
                    },
                    "options": [
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "All"
                            },
                            "value": "all"
                        },
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "✅ Completed"
                            },
                            "value": "completed"
                        },
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "📝 Assigned"
                            },
                            "value": "assigned"
                        },
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "🔄 In Progress"
                            },
                            "value": "in_progress"
                        }
                    ],
                    "action_id": "status_select"
                },
                "label": {
                    "type": "plain_text",
                    "text": "Status Filter"
                }
            }
        ]
    }

def create_assessment_report_modal(app_data):
    """Create modal for assessment report with only assessment selection"""
    
    # Get list of assessments
    assessment_options = []
    for assess_id, assess_data in app_data.get("assessments", {}).items():
        assessment_options.append({
            "text": {
                "type": "plain_text",
                "text": assess_data.get("name", "Unknown Assessment")
            },
            "value": str(assess_id)
        })
    
    if not assessment_options:
        assessment_options.append({
            "text": {
                "type": "plain_text",
                "text": "No assessments available"
            },
            "value": "none"
        })
    
    return {
        "type": "modal",
        "callback_id": "assessment_report_modal",
        "title": {
            "type": "plain_text",
            "text": "📋 Assessment Report"
        },
        "submit": {
            "type": "plain_text",
            "text": "Generate PDF"
        },
        "close": {
            "type": "plain_text",
            "text": "Cancel"
        },
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "📋 Assessment Report"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Generate a report showing all engineers assigned to a specific assessment."
                }
            },
            {
                "type": "divider"
            },
            {
                "type": "input",
                "block_id": "assessment_selection",
                "element": {
                    "type": "static_select",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "Select an assessment"
                    },
                    "options": assessment_options,
                    "action_id": "selected_assessment"
                },
                "label": {
                    "type": "plain_text",
                    "text": "Assessment"
                }
            },
            {
                "type": "input",
                "block_id": "status_filter",
                "optional": True,
                "element": {
                    "type": "static_select",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "Filter by status (optional)"
                    },
                    "options": [
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "All"
                            },
                            "value": "all"
                        },
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "✅ Completed"
                            },
                            "value": "completed"
                        },
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "📝 Assigned"
                            },
                            "value": "assigned"
                        },
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "🔄 In Progress"
                            },
                            "value": "in_progress"
                        }
                    ],
                    "action_id": "status_select"
                },
                "label": {
                    "type": "plain_text",
                    "text": "Status Filter"
                }
            }
        ]
    }

def create_due_report_modal():
    """Create modal for due report (no selections needed)"""
    
    return {
        "type": "modal",
        "callback_id": "due_report_modal",
        "title": {
            "type": "plain_text",
            "text": "⏰ Due Report"
        },
        "submit": {
            "type": "plain_text",
            "text": "Generate PDF"
        },
        "close": {
            "type": "plain_text",
            "text": "Cancel"
        },
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "⏰ Due Report - Behind Schedule"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Generate a report showing all engineers who are behind schedule on their assignments."
                }
            },
            {
                "type": "divider"
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "📊 *This report will include:*\n\n"
                           "• All overdue assignments\n"
                           "• Engineers affected\n"
                           "• Days overdue for each assignment\n"
                           "• Color-coded severity indicators:\n"
                           "  🔴 Red: >7 days overdue\n"
                           "  🟠 Orange: >3 days overdue\n"
                           "  🟡 Yellow: <3 days overdue\n"
                           "• Actionable recommendations"
                }
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": "Click 'Generate PDF' to create the report. No additional selections needed."
                    }
                ]
            }
        ]
    }

def create_detailed_report_modal(app_data):
    """Create modal for detailed reports with multiple report types - DEPRECATED, use create_report_type_selection_modal instead"""
    
    # Get list of engineers for selection
    engineer_options = []
    for eng_id, eng_data in app_data.get("engineers", {}).items():
        engineer_options.append({
            "text": {
                "type": "plain_text",
                "text": eng_data.get("name", "Unknown Engineer")
            },
            "value": str(eng_id)
        })
    
    # If no engineers, show message
    if not engineer_options:
        engineer_options.append({
            "text": {
                "type": "plain_text",
                "text": "No engineers available"
            },
            "value": "none"
        })
    
    # Get list of modules
    module_options = []
    # Add predefined modules
    predefined_modules = {
        "0": "Agentforce",
        "1": "Data Cloud",
        "2": "Apex",
        "3": "Integration",
        "4": "Message Queue",
        "5": "Deployments"
    }
    for mod_id, mod_name in predefined_modules.items():
        module_options.append({
            "text": {
                "type": "plain_text",
                "text": mod_name
            },
            "value": f"predefined_{mod_id}"
        })
    
    # Add custom modules
    for mod_id, mod_data in app_data.get("modules", {}).items():
        module_options.append({
            "text": {
                "type": "plain_text",
                "text": mod_data.get("name", "Unknown Module")
            },
            "value": str(mod_id)
        })
    
    if not module_options:
        module_options.append({
            "text": {
                "type": "plain_text",
                "text": "No modules available"
            },
            "value": "none"
        })
    
    # Get list of assessments
    assessment_options = []
    for assess_id, assess_data in app_data.get("assessments", {}).items():
        assessment_options.append({
            "text": {
                "type": "plain_text",
                "text": assess_data.get("name", "Unknown Assessment")
            },
            "value": str(assess_id)
        })
    
    if not assessment_options:
        assessment_options.append({
            "text": {
                "type": "plain_text",
                "text": "No assessments available"
            },
            "value": "none"
        })
    
    return {
        "type": "modal",
        "callback_id": "detailed_report_modal",
        "title": {
            "type": "plain_text",
            "text": "📊 Detailed Report"
        },
        "submit": {
            "type": "plain_text",
            "text": "Generate PDF"
        },
        "close": {
            "type": "plain_text",
            "text": "Cancel"
        },
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "📊 Generate Detailed Report"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*Select report type* and relevant filters to generate a comprehensive PDF report."
                }
            },
            {
                "type": "divider"
            },
            {
                "type": "input",
                "block_id": "report_type",
                "element": {
                    "type": "static_select",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "Select report type"
                    },
                    "options": [
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "👤 By Engineer"
                            },
                            "value": "by_engineer"
                        },
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "📚 By Module"
                            },
                            "value": "by_module"
                        },
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "📋 By Assessments"
                            },
                            "value": "by_assessments"
                        },
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "⏰ Due Report (Behind Schedule)"
                            },
                            "value": "due_report"
                        }
                    ],
                    "action_id": "report_type_select"
                },
                "label": {
                    "type": "plain_text",
                    "text": "Report Type"
                }
            },
            {
                "type": "input",
                "block_id": "engineer_selection",
                "optional": True,
                "element": {
                    "type": "static_select",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "Select an engineer (for By Engineer report)"
                    },
                    "options": engineer_options,
                    "action_id": "selected_engineer"
                },
                "label": {
                    "type": "plain_text",
                    "text": "Engineer (optional)"
                }
            },
            {
                "type": "input",
                "block_id": "module_selection",
                "optional": True,
                "element": {
                    "type": "static_select",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "Select a module (for By Module report)"
                    },
                    "options": module_options,
                    "action_id": "selected_module"
                },
                "label": {
                    "type": "plain_text",
                    "text": "Module (optional)"
                }
            },
            {
                "type": "input",
                "block_id": "assessment_selection",
                "optional": True,
                "element": {
                    "type": "static_select",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "Select an assessment (for By Assessments report)"
                    },
                    "options": assessment_options,
                    "action_id": "selected_assessment"
                },
                "label": {
                    "type": "plain_text",
                    "text": "Assessment (optional)"
                }
            },
            {
                "type": "input",
                "block_id": "status_filter",
                "optional": True,
                "element": {
                    "type": "static_select",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "Filter by status (optional)"
                    },
                    "options": [
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "All"
                            },
                            "value": "all"
                        },
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "✅ Completed"
                            },
                            "value": "completed"
                        },
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "📝 Assigned"
                            },
                            "value": "assigned"
                        },
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "🔄 In Progress"
                            },
                            "value": "in_progress"
                        }
                    ],
                    "action_id": "status_select"
                },
                "label": {
                    "type": "plain_text",
                    "text": "Status Filter"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "📄 *Report Types:*\n• *By Engineer:* Complete training report for a specific engineer\n• *By Module:* All engineers assigned to a specific module\n• *By Assessments:* All engineers assigned to specific assessments\n• *Due Report:* Engineers who are behind schedule on their assignments"
                }
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
                "text": f"{engineer_data.get('name', 'Unknown Engineer')} ({get_team(engineer_data)})"
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

def create_leaderboard_modal(app_data):
    """Create modal displaying leaderboard by Engineer and by Module"""
    
    # Calculate Engineer Leaderboard
    engineers_stats = []
    for engineer_id, engineer_data in app_data["engineers"].items():
        total_assignments = 0
        completed_assignments = 0
        
        for assign_id, assign_data in app_data["assignments"].items():
            if assign_data.get("engineer_id") == int(engineer_id):
                total_assignments += 1
                if assign_data.get("status") == "completed":
                    completed_assignments += 1
        
        if total_assignments > 0:  # Only include engineers with assignments
            completion_rate = (completed_assignments / total_assignments * 100)
            engineers_stats.append({
                "name": engineer_data.get("name", "Unknown Engineer"),
                "completion_rate": completion_rate,
                "completed": completed_assignments,
                "total": total_assignments
            })
    
    # Sort by completion rate
    engineers_stats.sort(key=lambda x: (-x["completion_rate"], -x["completed"]))
    
    # Calculate Module Leaderboard
    module_stats = {}
    predefined_modules = {
        "0": {"name": "Agentforce"},
        "1": {"name": "Data Cloud"},
        "2": {"name": "Apex"},
        "3": {"name": "Integration"},
        "4": {"name": "Message Queue"},
        "5": {"name": "Deployments"}
    }
    
    for assign_id, assign_data in app_data["assignments"].items():
        if assign_data.get("type") == "module":
            module_id = str(assign_data.get("module_id", ""))
            
            # Get module name from predefined modules or app_data
            if module_id in predefined_modules:
                module_name = predefined_modules[module_id]["name"]
            elif module_id in app_data.get("modules", {}):
                module_name = app_data["modules"][module_id].get("name", "Unknown Module")
            else:
                module_name = f"Module {module_id}"
            
            if module_name not in module_stats:
                module_stats[module_name] = {"total": 0, "completed": 0}
            
            module_stats[module_name]["total"] += 1
            if assign_data.get("status") == "completed":
                module_stats[module_name]["completed"] += 1
    
    # Convert to list and calculate completion rates
    modules_list = []
    for module_name, stats in module_stats.items():
        completion_rate = (stats["completed"] / stats["total"] * 100) if stats["total"] > 0 else 0
        modules_list.append({
            "name": module_name,
            "completion_rate": completion_rate,
            "completed": stats["completed"],
            "total": stats["total"]
        })
    
    # Sort by completion rate
    modules_list.sort(key=lambda x: (-x["completion_rate"], -x["completed"]))
    
    # Build modal blocks
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "🏆 Leaderboard",
                "emoji": True
            }
        },
        {
            "type": "divider"
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*📊 By Engineer*"
            }
        }
    ]
    
    # Add Engineer leaderboard entries
    if engineers_stats:
        for i, engineer in enumerate(engineers_stats[:10], 1):
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"*{i}.*"
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"{medal} *{engineer['name']}*\n"
                           f"├ Completion Rate: *{engineer['completion_rate']:.1f}%*\n"
                           f"└ Completed: {engineer['completed']}/{engineer['total']} assignments"
                }
            })
    else:
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "_No engineer data available yet._"
            }
        })
    
    # Add Module leaderboard section
    blocks.extend([
        {
            "type": "divider"
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*📚 By Module*"
            }
        }
    ])
    
    # Add Module leaderboard entries
    if modules_list:
        for i, module in enumerate(modules_list[:10], 1):
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"*{i}.*"
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"{medal} *{module['name']}*\n"
                           f"├ Completion Rate: *{module['completion_rate']:.1f}%*\n"
                           f"└ Completed: {module['completed']}/{module['total']} times"
                }
            })
    else:
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "_No module data available yet._"
            }
        })
    
    return {
        "type": "modal",
        "title": {
            "type": "plain_text",
            "text": "🏆 Leaderboard",
            "emoji": True
        },
        "close": {
            "type": "plain_text",
            "text": "Close",
            "emoji": True
        },
        "blocks": blocks
    }
