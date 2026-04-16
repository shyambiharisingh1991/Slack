import json

def create_home_view(user_id, app_data):
    """Create the home tab view with dashboard interface"""
    
    # Get user's engineer record
    engineer = None
    for eng_id, eng_data in app_data["engineers"].items():
        if eng_data.get("slack_user_id") == user_id:
            engineer = eng_data
            engineer["id"] = eng_id
            break
    
    # Get statistics
    total_engineers = len(app_data["engineers"])
    total_modules = len(app_data["modules"])
    pending_requests = 0
    for progress in app_data["progress"].values():
        if progress.get("unlock_requested") and not progress.get("unlock_approved"):
            pending_requests += 1
    
    # Get recent assignments if user is an engineer
    assignments = []
    if engineer:
        engineer_assignments = []
        for assign_id, assign_data in app_data["assignments"].items():
            if assign_data.get("engineer_id") == int(engineer["id"]):
                engineer_assignments.append(assign_data)
        assignments = engineer_assignments[:3]  # Limit to 3
    
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "🎓 Learning Management System"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "Welcome! Here you can manage new engineers, assign training modules, and track team progress."
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
                        "text": "➕ Add New Engineer"
                    },
                    "style": "primary",
                    "action_id": "add_engineer_button"
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "📚 Assign Module"
                    },
                    "action_id": "assign_module_button"
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "📋 Assessments"
                    },
                    "action_id": "assign_assessment_button"
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "📊 View Detailed Report"
                    },
                    "action_id": "detailed_report_button"
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "⚙️ Configurations"
                    },
                    "action_id": "configurations_button"
                }
            ]
        },
        {
            "type": "divider"
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"*👥 Total Engineers:*\n{total_engineers}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*📚 Total Modules:*\n{total_modules}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*⏳ Pending Requests:*\n{pending_requests}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*📈 System Status:*\n🟢 Active"
                }
            ]
        }
    ]
    
    # Add engineer progress if user is an engineer
    if engineer:
        # Add engineer-specific buttons
        blocks.extend([
            {
                "type": "divider"
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"👤 *Engineer Dashboard*"
                }
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "📝 View My Assignments"
                        },
                        "style": "primary",
                        "action_id": "view_assignments_button"
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "🏆 Leaderboard"
                        },
                        "action_id": "leaderboard_button"
                    }
                ]
            }
        ])
        
        # Get all assignments for this engineer
        engineer_assignments = []
        for assign_id, assign_data in app_data["assignments"].items():
            if assign_data.get("engineer_id") == int(engineer["id"]):
                engineer_assignments.append(assign_data)
        
        if engineer_assignments:
            completed_count = len([a for a in engineer_assignments if a.get("status") == "completed"])
            total_count = len(engineer_assignments)
            progress_percent = int((completed_count / total_count) * 100) if total_count > 0 else 0
            
            # Get current in-progress assignment
            current_assignment = None
            for assign_id, assign_data in app_data["assignments"].items():
                if assign_data.get("engineer_id") == int(engineer["id"]) and assign_data.get("status") == "in_progress":
                    current_assignment = assign_data
                    break
            
            current_module_name = "No active module"
            if current_assignment:
                module_id = current_assignment.get("module_id")
                if module_id and str(module_id) in app_data["modules"]:
                    current_module_name = app_data["modules"][str(module_id)].get("name", "Unknown Module")
            
            blocks.extend([
                {
                    "type": "divider"
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"👤 *{engineer.get('name', 'Unknown Engineer')}* | {engineer.get('team', 'guides')}"
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Progress:*\n{'█' * int(progress_percent/10)}{'░' * (10-int(progress_percent/10))} {progress_percent}% ({completed_count}/{total_count} modules)"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Current Module:*\n{current_module_name}"
                        }
                    ]
                }
            ])
    
    # Add pending unlock requests section
    if pending_requests > 0:
        blocks.extend([
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"⏳ *Pending Unlock Requests ({pending_requests})*"
                },
                "accessory": {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "Collapse"
                    },
                    "action_id": "collapse_requests"
                }
            }
        ])
        
        # Get pending requests
        pending_list = []
        for progress_id, progress_data in app_data["progress"].items():
            if progress_data.get("unlock_requested") and not progress_data.get("unlock_approved"):
                pending_list.append((progress_id, progress_data))
        
        for progress_id, request in pending_list[:5]:  # Limit to 5
            engineer_id = request.get("engineer_id")
            assignment_id = request.get("assignment_id")
            
            engineer_name = "Unknown Engineer"
            if engineer_id and str(engineer_id) in app_data["engineers"]:
                engineer_name = app_data["engineers"][str(engineer_id)].get("name", "Unknown Engineer")
            
            module_name = "Unknown Module"
            if assignment_id and str(assignment_id) in app_data["assignments"]:
                assignment = app_data["assignments"][str(assignment_id)]
                module_id = assignment.get("module_id")
                if module_id and str(module_id) in app_data["modules"]:
                    module_name = app_data["modules"][str(module_id)].get("name", "Unknown Module")
            
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"{engineer_name} requested to unlock {module_name}"
                },
                "accessory": {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "Approve"
                    },
                    "style": "primary",
                    "action_id": f"approve_unlock_{progress_id}"
                }
            })
    
    return {
        "type": "home",
        "blocks": blocks
    }
