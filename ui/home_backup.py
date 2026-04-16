import json
from auth import is_admin, get_user_role

def create_home_view(user_id, app_data, selected_engineer_id=None):
    """Create the home tab view with dashboard interface
    
    Args:
        user_id: The Slack user ID viewing the home tab
        app_data: The application data dictionary
        selected_engineer_id: Optional engineer ID to display details for in the dropdown
    """
    
    # Check if user is admin
    user_is_admin = is_admin(user_id, app_data)
    user_role = get_user_role(user_id, app_data)
    
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
    
    # Role-based welcome message
    role_display = "Administrator" if user_role == "admin" else "Manager" if user_role == "manager" else "Engineer"
    welcome_text = f"Welcome! "
    if user_is_admin:
        welcome_text += "As a **" + role_display + "**, you can manage engineers, assign training modules, and track team progress."
    else:
        welcome_text += "View your assignments, track your progress, and access learning resources."
    
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
                "text": welcome_text
            }
        },
        {
            "type": "divider"
        }
    ]
    
    # Admin-only action buttons
    if user_is_admin:
        admin_buttons = {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "🔄 Refresh"
                    },
                    "action_id": "refresh_home_button"
                },
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
                        "text": "🏆 Leaderboard"
                    },
                    "action_id": "leaderboard_button"
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
        }
        blocks.append(admin_buttons)
    else:
        # Non-admin users see refresh, leaderboard, and assignments
        user_buttons = {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "🔄 Refresh"
                    },
                    "action_id": "refresh_home_button"
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "🏆 Leaderboard"
                    },
                    "action_id": "leaderboard_button"
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "📋 View My Assignments"
                    },
                    "action_id": "view_assignments_button"
                }
            ]
        }
        blocks.append(user_buttons)
    
    blocks.append({"type": "divider"})
    
    # System statistics (show to all users)
    blocks.append({
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
    })
    
    # Add engineer summary section for admins
    if user_is_admin:
        blocks.append({"type": "divider"})
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "👥 *Engineer Progress Summary*"
            }
        })
        
        # Get all engineers and their assignment status
        engineer_summary = []
        for eng_id, eng_data in app_data["engineers"].items():
            eng_assignments = []
            for assign_id, assign_data in app_data["assignments"].items():
                if assign_data.get("engineer_id") == int(eng_id):
                    eng_assignments.append(assign_data)
            
            if eng_assignments:  # Only show engineers with assignments
                total = len(eng_assignments)
                completed = len([a for a in eng_assignments if a.get("status") == "completed"])
                in_progress = len([a for a in eng_assignments if a.get("status") == "in_progress"])
                assigned = len([a for a in eng_assignments if a.get("status") == "assigned"])
                
                # Get incomplete assignments
                incomplete = total - completed
                
                # Check if there's a pending acknowledgment
                ping_acks = app_data.get("ping_acknowledgments", {})
                engineer_ack_key = f"engineer_{eng_id}"
                last_ack = ping_acks.get(engineer_ack_key, {})
                ack_status = last_ack.get("status", "none")
                ack_timestamp = last_ack.get("timestamp", "")
                
                engineer_summary.append({
                    "id": eng_id,
                    "name": eng_data.get("name", "Unknown"),
                    "total": total,
                    "completed": completed,
                    "in_progress": in_progress,
                    "assigned": assigned,
                    "incomplete": incomplete,
                    "ack_status": ack_status,
                    "ack_timestamp": ack_timestamp
                })
        
        # Sort by incomplete count (most incomplete first)
        engineer_summary.sort(key=lambda x: x["incomplete"], reverse=True)
        
        if engineer_summary:
            # Create dropdown options
            dropdown_options = []
            for eng in engineer_summary:
                dropdown_options.append({
                    "text": {
                        "type": "plain_text",
                        "text": f"{eng['name']} ({eng['completed']}/{eng['total']} complete)"
                    },
                    "value": eng["id"]
                })
            
            # Auto-select first engineer if none selected
            if not selected_engineer_id and engineer_summary:
                selected_engineer_id = engineer_summary[0]["id"]
            
            # Add dropdown to select engineer
            dropdown_block = {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*Select an engineer to view their progress:*"
                },
                "accessory": {
                    "type": "static_select",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "Choose an engineer"
                    },
                    "options": dropdown_options,
                    "action_id": "select_engineer_progress"
                }
            }
            
            # Set initial option if engineer is selected
            if selected_engineer_id:
                for eng in engineer_summary:
                    if eng["id"] == selected_engineer_id:
                        dropdown_block["accessory"]["initial_option"] = {
                            "text": {
                                "type": "plain_text",
                                "text": f"{eng['name']} ({eng['completed']}/{eng['total']} complete)"
                            },
                            "value": eng["id"]
                        }
                        break
            
            blocks.append(dropdown_block)
            
            # Show details for selected engineer
            if selected_engineer_id:
                selected_eng = None
                for eng in engineer_summary:
                    if eng["id"] == selected_engineer_id:
                        selected_eng = eng
                        break
                
                if selected_eng:
                    completion_rate = (selected_eng["completed"] / selected_eng["total"] * 100) if selected_eng["total"] > 0 else 0
                    
                    # Status indicators
                    status_text = f"✅ {selected_eng['completed']} | 🔄 {selected_eng['in_progress']} | 📝 {selected_eng['assigned']}"
                    
                    # Acknowledgment status
                    ack_display = ""
                    if selected_eng["ack_status"] == "acknowledged":
                        ack_display = f"\n🔔 *Ping Acknowledged* ({selected_eng['ack_timestamp'][:10]})"
                    elif selected_eng["ack_status"] == "pending":
                        ack_display = f"\n⏳ *Ping Sent* (awaiting acknowledgment)"
                    
                    # Progress bar
                    progress_bar = "█" * int(completion_rate / 10) + "░" * (10 - int(completion_rate / 10))
                    
                    details_block = {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*📊 {selected_eng['name']}'s Progress*\n\n{progress_bar} {completion_rate:.0f}%\n\n{status_text}{ack_display}"
                        }
                    }
                    
                    # Add ping button if there are incomplete assignments
                    if selected_eng["incomplete"] > 0:
                        ping_button = {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "📍 Ping Engineer"
                            },
                            "action_id": f"ping_engineer_{selected_eng['id']}"
                        }
                        # Only add style if not acknowledged
                        if selected_eng["ack_status"] != "acknowledged":
                            ping_button["style"] = "primary"
                        
                        details_block["accessory"] = ping_button
                    
                    blocks.append(details_block)
        else:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "_No engineers with assignments yet._"
                }
            })
    
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
