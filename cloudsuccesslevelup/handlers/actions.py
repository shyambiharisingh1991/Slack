from datetime import datetime
import json
import re

def register_actions(app, get_app_data, save_data):
    """Register all action handlers"""
    
    @app.action("add_engineer_button")
    def handle_add_engineer_button(ack, body, client):
        ack()
        try:
            from ui.modals import create_engineer_modal
            client.views_open(
                trigger_id=body["trigger_id"],
                view=create_engineer_modal()
            )
        except Exception as e:
            print(f"Error opening engineer modal: {e}")

    @app.action("assign_module_button")
    def handle_assign_module_button(ack, body, client):
        ack()
        try:
            app_data = get_app_data()
            from ui.modals import create_assign_module_modal
            client.views_open(
                trigger_id=body["trigger_id"],
                view=create_assign_module_modal(app_data)
            )
        except Exception as e:
            print(f"Error opening assign module modal: {e}")

    @app.action("assign_assessment_button")
    def handle_assign_assessment_button(ack, body, client):
        ack()
        try:
            app_data = get_app_data()
            from ui.modals import create_assign_assessment_modal
            client.views_open(
                trigger_id=body["trigger_id"],
                view=create_assign_assessment_modal(app_data)
            )
        except Exception as e:
            print(f"Error opening assessment assignment modal: {e}")

    @app.action("detailed_report_button")
    def handle_detailed_report_button(ack, body, client):
        ack()
        try:
            app_data = get_app_data()
            from ui.modals import create_detailed_report_modal
            client.views_open(
                trigger_id=body["trigger_id"],
                view=create_detailed_report_modal(app_data)
            )
        except Exception as e:
            print(f"Error opening detailed report modal: {e}")

    @app.action("configurations_button")
    def handle_configurations_button(ack, body, client):
        ack()
        try:
            app_data = get_app_data()
            from ui.configurations import create_configurations_view
            client.views_publish(
                user_id=body["user"]["id"],
                view=create_configurations_view(body["user"]["id"], app_data)
            )
        except Exception as e:
            print(f"Error opening configurations tab: {e}")

    @app.action("view_assignments_button")
    def handle_view_assignments(ack, body, client):
        ack()
        
        try:
            app_data = get_app_data()
            user_id = body["user"]["id"]
            
            # Find user in engineers (they might have been auto-created during assignment)
            engineer = None
            for eng_id, eng_data in app_data["engineers"].items():
                if eng_data.get("slack_user_id") == user_id:
                    engineer = eng_data
                    engineer["id"] = eng_id
                    break
            
            # If user not found, they have no assignments yet
            if not engineer:
                client.chat_postMessage(
                    channel=user_id,
                    text="📝 No assignments found. You haven't been assigned any modules or assessments yet."
                )
                return
            
            # Get assignments for this engineer
            assignments = []
            for assign_id, assign_data in app_data["assignments"].items():
                if assign_data.get("engineer_id") == int(engineer["id"]):
                    assignments.append(assign_data)
            
            # Debug logging
            print(f"Found {len(assignments)} assignments for engineer {engineer['id']} ({engineer['name']})")
            print(f"Total assignments in system: {len(app_data['assignments'])}")
            for assign_id, assign_data in app_data["assignments"].items():
                print(f"Assignment {assign_id}: engineer_id={assign_data.get('engineer_id')}, module_id={assign_data.get('module_id')}")
            
            if not assignments:
                client.chat_postMessage(
                    channel=user_id,
                    text="📝 No assignments found."
                )
                return
            
            blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "📝 Your Assignments"
                    }
                }
            ]
            
            for assignment in assignments:
                progress_percent = 0
                for progress_id, progress_data in app_data["progress"].items():
                    if progress_data.get("assignment_id") == assignment["id"]:
                        progress_percent = progress_data.get("progress_percentage", 0)
                        break
                
                status_emoji = {
                    "assigned": "🆕",
                    "in_progress": "🔄",
                    "completed": "✅",
                    "overdue": "⚠️",
                    "locked": "🔒"
                }
                
                # Get module/assessment name
                item_name = "Unknown Item"
                module_id = assignment.get("module_id")
                assignment_type = assignment.get("type", "module")
                
                if assignment_type == "assessment":
                    # Look in assessments
                    if module_id and str(module_id) in app_data["assessments"]:
                        item_name = app_data["assessments"][str(module_id)].get("name", "Unknown Assessment")
                    else:
                        item_name = "Unknown Assessment"
                else:
                    # Look in modules
                    if module_id and str(module_id) in app_data["modules"]:
                        item_name = app_data["modules"][str(module_id)].get("name", "Unknown Module")
                    else:
                        item_name = "Unknown Module"
                
                # Check if module is locked
                is_locked = assignment.get("status") == "locked"
                locked_reason = assignment.get("locked_reason", "")
                
                # Debug logging
                print(f"Assignment {assignment['id']}: status={assignment.get('status')}, is_locked={is_locked}, sequence_order={assignment.get('sequence_order')}")
                
                # Create the text content
                item_emoji = "📋" if assignment_type == "assessment" else "📚"
                status_text = f"{status_emoji.get(assignment.get('status', 'assigned'), item_emoji)} *{item_name}*\n"
                status_text += f"Type: {assignment_type.title()}\n"
                status_text += f"Progress: {progress_percent}%\n"
                status_text += f"Status: {assignment.get('status', 'assigned').title()}\n"
                status_text += f"Due: {assignment.get('due_date', 'No due date')}"
                
                if is_locked:
                    status_text += f"\n🔒 Locked"
                
                # Create the button (different for modules vs assessments)
                if assignment_type == "assessment":
                    button_text = "🔒 Locked" if is_locked else "📋 Start Assessment"
                    button_style = "danger" if is_locked else "primary"
                    button_action = "locked_assessment" if is_locked else "start_assessment"
                else:
                    button_text = "🔒 Locked" if is_locked else "Update Progress"
                    button_style = "danger" if is_locked else "primary"
                    button_action = "locked_module" if is_locked else "update_progress"
                
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": status_text
                    },
                    "accessory": {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": button_text
                        },
                        "action_id": f"{button_action}_{assignment['id']}" if not is_locked else button_action,
                        "style": button_style
                    }
                })
            
            client.chat_postMessage(
                channel=user_id,
                blocks=blocks
            )
            
        except Exception as e:
            print(f"Error viewing assignments: {e}")

    @app.action("leaderboard_button")
    def handle_leaderboard(ack, body, client):
        ack()
        
        try:
            app_data = get_app_data()
            # Get engineers with their completion stats
            engineers_stats = []
            for engineer_id, engineer_data in app_data["engineers"].items():
                total_assignments = 0
                completed_assignments = 0
                
                for assign_id, assign_data in app_data["assignments"].items():
                    if assign_data.get("engineer_id") == int(engineer_id):
                        total_assignments += 1
                        if assign_data.get("status") == "completed":
                            completed_assignments += 1
                
                completion_rate = (completed_assignments / total_assignments * 100) if total_assignments > 0 else 0
                
                engineers_stats.append({
                    "name": engineer_data.get("name", "Unknown Engineer"),
                    "completion_rate": completion_rate,
                    "completed": completed_assignments,
                    "total": total_assignments
                })
            
            # Sort by completion rate
            engineers_stats.sort(key=lambda x: x["completion_rate"], reverse=True)
            
            blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "🏆 Team Leaderboard"
                    }
                }
            ]
            
            for i, engineer in enumerate(engineers_stats[:10], 1):
                medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"{medal} *{engineer['name']}*\n"
                               f"Completion Rate: {engineer['completion_rate']:.1f}%\n"
                               f"Completed: {engineer['completed']}/{engineer['total']} assignments"
                    }
                })
            
            client.chat_postMessage(
                channel=body["user"]["id"],
                blocks=blocks
            )
            
        except Exception as e:
            print(f"Error generating leaderboard: {e}")

    # Modal form interaction handlers
    @app.action("slack_user_select")
    def handle_slack_user_select(ack, body, logger):
        ack()
        logger.info("User selected from dropdown")

    @app.action("team_select")
    def handle_team_select(ack, body, logger):
        ack()
        logger.info("Team selected from dropdown")

    @app.action("geo_select")
    def handle_geo_select(ack, body, logger):
        ack()
        logger.info("Geo selected from dropdown")

    @app.action("plan_select")
    def handle_plan_select(ack, body, logger):
        ack()
        logger.info("Plan selected from dropdown")

    # Modal interaction handlers - these handle actions within modals
    @app.action("engineer_select")
    def handle_engineer_select(ack, body, logger):
        ack()
        # Check if this is from a modal
        if body.get('view'):
            logger.info(f"Engineer selected in modal: {body.get('view', {}).get('callback_id', 'unknown')}")
        else:
            logger.info("Engineer selected from dropdown")

    @app.action("module_select")
    def handle_module_select(ack, body, logger):
        ack()
        # Check if this is from a modal
        if body.get('view'):
            logger.info(f"Module selected in modal: {body.get('view', {}).get('callback_id', 'unknown')}")
        else:
            logger.info("Module selected from dropdown")

    @app.action("assessment_select")
    def handle_assessment_select(ack, body, logger):
        ack()
        # Check if this is from a modal
        if body.get('view'):
            logger.info(f"Assessment selected in modal: {body.get('view', {}).get('callback_id', 'unknown')}")
        else:
            logger.info("Assessment selected from dropdown")

    @app.action("due_date_picker")
    def handle_due_date_picker(ack, body, logger):
        ack()
        # Check if this is from a modal
        if body.get('view'):
            logger.info(f"Due date selected in modal: {body.get('view', {}).get('callback_id', 'unknown')}")
        else:
            logger.info("Due date selected")

    @app.action("progress_select")
    def handle_progress_select(ack, body, logger):
        ack()
        # Check if this is from a modal
        if body.get('view'):
            logger.info(f"Progress selected in modal: {body.get('view', {}).get('callback_id', 'unknown')}")
        else:
            logger.info("Progress percentage selected")

    @app.action("notes_input")
    def handle_notes_input(ack, body, logger):
        ack()
        # Check if this is from a modal
        if body.get('view'):
            logger.info(f"Notes updated in modal: {body.get('view', {}).get('callback_id', 'unknown')}")
        else:
            logger.info("Notes input updated")

    # Module action handlers

    @app.action("locked_module")
    def handle_locked_module(ack, body, client):
        ack()
        try:
            # Create a modal to show the locked message
            modal = {
                "type": "modal",
                "callback_id": "locked_module_modal",
                "title": {
                    "type": "plain_text",
                    "text": "🔒 Module Locked"
                },
                "close": {
                    "type": "plain_text",
                    "text": "OK"
                },
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "🔒 *This module is locked*\n\nComplete the previous module to unlock this one."
                        }
                    },
                    {
                        "type": "context",
                        "elements": [
                            {
                                "type": "mrkdwn",
                                "text": "Modules are unlocked sequentially. Finish the current module to proceed to the next one."
                            }
                        ]
                    }
                ]
            }
            
            client.views_open(
                trigger_id=body["trigger_id"],
                view=modal
            )
        except Exception as e:
            print(f"Error showing locked module modal: {e}")
            client.chat_postMessage(
                channel=body["user"]["id"],
                text="🔒 This module is locked. Complete the previous module to unlock this one."
            )

    # Progress update handlers
    @app.action(re.compile(r"update_progress_\d+"))
    def handle_update_progress(ack, body, client):
        ack()
        try:
            app_data = get_app_data()
            # Extract assignment ID from action_id
            action_id = body["actions"][0]["action_id"]
            assignment_id = action_id.split("_")[-1]
            
            # Get assignment details
            assignment = None
            for assign_id, assign_data in app_data["assignments"].items():
                if str(assign_data["id"]) == assignment_id:
                    assignment = assign_data
                    break
            
            if not assignment:
                client.chat_postMessage(
                    channel=body["user"]["id"],
                    text="❌ Assignment not found."
                )
                return
            
            # Check if module is locked
            if assignment.get("status") == "locked":
                locked_reason = assignment.get("locked_reason", "Complete previous module to unlock")
                client.chat_postMessage(
                    channel=body["user"]["id"],
                    text=f"🔒 This module is locked. {locked_reason}"
                )
                return
            
            # Get module details
            module_name = "Unknown Module"
            module_id = assignment.get("module_id")
            if module_id and str(module_id) in app_data["modules"]:
                module_name = app_data["modules"][str(module_id)].get("name", "Unknown Module")
            
            # Send progress update modal
            from ui.modals import create_progress_update_modal
            client.views_open(
                trigger_id=body["trigger_id"],
                view=create_progress_update_modal(assignment_id, module_name)
            )
            
        except Exception as e:
            print(f"Error updating progress: {e}")
            client.chat_postMessage(
                channel=body["user"]["id"],
                text="❌ Error updating progress. Please try again."
            )

    @app.action(re.compile(r"start_assessment_\d+"))
    def handle_start_assessment(ack, body, client):
        ack()
        try:
            app_data = get_app_data()
            user_id = body["user"]["id"]
            
            # Extract assignment ID from action_id
            action_id = body["actions"][0]["action_id"]
            assignment_id = action_id.split("_")[-1]
            
            # Debug logging
            print(f"Looking for assignment_id: {assignment_id}")
            print(f"Available assignments: {list(app_data['assignments'].keys())}")
            print(f"Assignment data: {app_data['assignments']}")
            
            # Get assignment details
            assignment = app_data["assignments"].get(assignment_id)
            if not assignment:
                # Try to find assignment by ID in the assignment data
                for assign_key, assign_data in app_data["assignments"].items():
                    print(f"Checking assignment {assign_key}: id={assign_data.get('id')}, status={assign_data.get('status')}")
                    if str(assign_data.get("id")) == assignment_id:
                        assignment = assign_data
                        break
                
                if not assignment:
                    print(f"Assignment {assignment_id} not found in any format")
                    client.chat_postMessage(
                        channel=user_id,
                        text="❌ Assignment not found."
                    )
                    return
            
            # Get assessment details
            assessment_id = assignment.get("module_id")
            assessment = app_data["assessments"].get(str(assessment_id))
            if not assessment:
                client.chat_postMessage(
                    channel=user_id,
                    text="❌ Assessment not found."
                )
                return
            
            # Check if assessment is already completed (temporarily disabled for debugging)
            # if assignment.get("status") == "completed":
            #     # Find progress data for this assignment
            #     progress_data = None
            #     for progress_id, progress in app_data["progress"].items():
            #         if progress.get("assignment_id") == int(assignment_id):
            #             progress_data = progress
            #             break
            #     
            #     if progress_data:
            #         # Show completion status modal
            #         from ui.assessment_modal import create_assessment_completion_modal
            #         completion_modal = create_assessment_completion_modal(assignment, assessment, progress_data)
            #         client.views_open(
            #             trigger_id=body["trigger_id"],
            #             view=completion_modal
            #         )
            #         return
            #     else:
            #         # Fallback - just show completion message
            #         client.chat_postMessage(
            #             channel=user_id,
            #             text="✅ This assessment has already been completed."
            #         )
            #         return
            
            # Open assessment modal
            from ui.assessment_modal import create_assessment_modal
            client.views_open(
                trigger_id=body["trigger_id"],
                view=create_assessment_modal(assessment, assignment_id)
            )
        except Exception as e:
            print(f"Error opening assessment: {e}")
            client.chat_postMessage(
                channel=body["user"]["id"],
                text="❌ Error opening assessment. Please try again."
            )

    @app.action(re.compile(r"retake_assessment_\d+"))
    def handle_retake_assessment(ack, body, client):
        ack()
        try:
            app_data = get_app_data()
            user_id = body["user"]["id"]
            
            # Extract assignment ID from action_id
            action_id = body["actions"][0]["action_id"]
            assignment_id = action_id.split("_")[-1]
            
            # Get assignment details
            assignment = app_data["assignments"].get(assignment_id)
            if not assignment:
                # Try to find assignment by ID in the assignment data
                for assign_key, assign_data in app_data["assignments"].items():
                    if str(assign_data.get("id")) == assignment_id:
                        assignment = assign_data
                        break
                
                if not assignment:
                    client.chat_postMessage(
                        channel=user_id,
                        text="❌ Assignment not found."
                    )
                    return
            
            # Get assessment details
            assessment_id = assignment.get("module_id")
            assessment = app_data["assessments"].get(str(assessment_id))
            if not assessment:
                client.chat_postMessage(
                    channel=user_id,
                    text="❌ Assessment not found."
                )
                return
            
            # Reset assignment status for retake
            assignment["status"] = "assigned"
            assignment["retake_count"] = assignment.get("retake_count", 0) + 1
            assignment["retake_at"] = datetime.now().isoformat()
            
            # Remove old progress data
            for progress_id, progress in list(app_data["progress"].items()):
                if progress.get("assignment_id") == int(assignment_id):
                    del app_data["progress"][progress_id]
            
            save_data(app_data)
            
            # Open assessment modal for retake
            from ui.assessment_modal import create_assessment_modal
            client.views_open(
                trigger_id=body["trigger_id"],
                view=create_assessment_modal(assessment, assignment_id)
            )
            
        except Exception as e:
            print(f"Error retaking assessment: {e}")
            client.chat_postMessage(
                channel=body["user"]["id"],
                text="❌ Error retaking assessment. Please try again."
            )

    @app.action(re.compile(r"materials_accessed_\d+"))
    def handle_materials_accessed(ack, body, client):
        ack()
        try:
            app_data = get_app_data()
            user_id = body["user"]["id"]
            
            # Extract assignment ID from action_id
            action_id = body["actions"][0]["action_id"]
            assignment_id = action_id.split("_")[-1]
            
            # Debug logging
            print(f"Materials accessed clicked by user {user_id} for assignment {assignment_id}")
            print(f"Action ID: {action_id}")
            
            # Store that materials were accessed for this user
            if "materials_accessed" not in app_data:
                app_data["materials_accessed"] = {}
            
            app_data["materials_accessed"][user_id] = {
                "accessed_at": datetime.now().isoformat(),
                "assignment_id": assignment_id
            }
            
            print(f"Stored materials access: {app_data['materials_accessed'][user_id]}")
            save_data(app_data)
            
            # Update the button to show it was clicked
            client.chat_postMessage(
                channel=user_id,
                text="✅ Learning materials accessed! You can now complete the module."
            )
        except Exception as e:
            print(f"Error handling materials accessed: {e}")

    @app.action(re.compile(r"start_module_\d+"))
    def handle_start_module(ack, body, client):
        ack()
        try:
            app_data = get_app_data()
            user_id = body["user"]["id"]
            
            # Extract assignment ID from action_id
            action_id = body["actions"][0]["action_id"]
            assignment_id = action_id.split("_")[-1]
            
            # Get assignment details
            assignment = app_data["assignments"].get(assignment_id)
            if not assignment:
                # Try to find assignment by ID in the assignment data
                for assign_key, assign_data in app_data["assignments"].items():
                    if str(assign_data.get("id")) == assignment_id:
                        assignment = assign_data
                        break
                
                if not assignment:
                    client.chat_postMessage(
                        channel=user_id,
                        text="❌ Assignment not found."
                    )
                    return
            
            # Check if it's a module assignment
            if assignment.get("type") != "module":
                client.chat_postMessage(
                    channel=user_id,
                    text="❌ This is not a module assignment."
                )
                return
            
            # Open module start modal
            from ui.module_modal import create_module_start_modal
            client.views_open(
                trigger_id=body["trigger_id"],
                view=create_module_start_modal(
                    assignment.get("module_name", "Unknown Module"),
                    assignment.get("module_description", "No description"),
                    assignment.get("due_date", "No due date"),
                    assignment_id
                )
            )
            
        except Exception as e:
            print(f"Error opening module: {e}")
            client.chat_postMessage(
                channel=body["user"]["id"],
                text="❌ Error opening module. Please try again."
            )

    # Report action handlers
    @app.action("report_by_engineer")
    def handle_report_by_engineer(ack, body, client):
        ack()
        try:
            app_data = get_app_data()
            from ui.modals import create_engineer_selection_modal
            client.views_open(
                trigger_id=body["trigger_id"],
                view=create_engineer_selection_modal(app_data)
            )
        except Exception as e:
            print(f"Error opening engineer selection modal: {e}")

    @app.action("report_by_module")
    def handle_report_by_module(ack, body, client):
        ack()
        try:
            app_data = get_app_data()
            from ui.modals import create_module_selection_modal
            client.views_open(
                trigger_id=body["trigger_id"],
                view=create_module_selection_modal(app_data)
            )
        except Exception as e:
            print(f"Error opening module selection modal: {e}")

    @app.action("report_by_assessment")
    def handle_report_by_assessment(ack, body, client):
        ack()
        try:
            app_data = get_app_data()
            from ui.modals import create_assessment_selection_modal
            client.views_open(
                trigger_id=body["trigger_id"],
                view=create_assessment_selection_modal(app_data)
            )
        except Exception as e:
            print(f"Error opening assessment selection modal: {e}")

    # Additional action handlers for modal interactions
    @app.action("selected_engineer")
    def handle_selected_engineer(ack, body, logger):
        ack()
        logger.info("Engineer selected for report")

    @app.action("selected_module")
    def handle_selected_module(ack, body, logger):
        ack()
        logger.info("Module selected for report")

    @app.action("selected_assessment")
    def handle_selected_assessment(ack, body, logger):
        ack()
        logger.info("Assessment selected for report")

    @app.action("view_engineer_report")
    def handle_view_engineer_report(ack, body, client):
        ack()
        try:
            app_data = get_app_data()
            # Get selected engineer from the modal
            selected_engineer_id = None
            if body.get('view') and body['view'].get('state', {}).get('values'):
                values = body['view']['state']['values']
                if 'engineer_selection' in values and 'selected_engineer' in values['engineer_selection']:
                    selected_engineer_id = values['engineer_selection']['selected_engineer']['selected_option']['value']
            
            if not selected_engineer_id:
                client.chat_postMessage(
                    channel=body["user"]["id"],
                    text="❌ Please select an engineer first."
                )
                return
            
            # Get engineer details
            engineer = app_data["engineers"].get(selected_engineer_id)
            if not engineer:
                client.chat_postMessage(
                    channel=body["user"]["id"],
                    text="❌ Engineer not found."
                )
                return
            
            # Generate report for the engineer
            assignments = []
            for assign_id, assign_data in app_data["assignments"].items():
                if assign_data.get("engineer_id") == int(selected_engineer_id):
                    assignments.append(assign_data)
            
            blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"📊 Report for {engineer.get('name', 'Unknown Engineer')}"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Team:* {engineer.get('team', 'Unknown')}\n*Location:* {engineer.get('geo', 'Unknown')}\n*Onboarding Plan:* {engineer.get('onboarding_plan', 'Unknown')}"
                    }
                }
            ]
            
            if assignments:
                blocks.append({"type": "divider"})
                for assignment in assignments:
                    module_name = "Unknown Module"
                    module_id = assignment.get("module_id")
                    if module_id and str(module_id) in app_data["modules"]:
                        module_name = app_data["modules"][str(module_id)].get("name", "Unknown Module")
                    
                    blocks.append({
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"📚 *{module_name}*\nStatus: {assignment.get('status', 'Unknown').title()}\nDue: {assignment.get('due_date', 'No due date')}"
                        }
                    })
            else:
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "No assignments found for this engineer."
                    }
                })
            
            client.chat_postMessage(
                channel=body["user"]["id"],
                blocks=blocks
            )
            
        except Exception as e:
            print(f"Error generating engineer report: {e}")
            client.chat_postMessage(
                channel=body["user"]["id"],
                text="❌ Error generating report. Please try again."
            )

    @app.action("view_module_report")
    def handle_view_module_report(ack, body, client):
        ack()
        try:
            app_data = get_app_data()
            # Get selected module from the modal
            selected_module_id = None
            if body.get('view') and body['view'].get('state', {}).get('values'):
                values = body['view']['state']['values']
                if 'module_selection' in values and 'selected_module' in values['module_selection']:
                    selected_module_id = values['module_selection']['selected_module']['selected_option']['value']
            
            if not selected_module_id:
                client.chat_postMessage(
                    channel=body["user"]["id"],
                    text="❌ Please select a module first."
                )
                return
            
            # Get module details
            module = app_data["modules"].get(selected_module_id)
            if not module:
                client.chat_postMessage(
                    channel=body["user"]["id"],
                    text="❌ Module not found."
                )
                return
            
            # Generate report for the module
            assignments = []
            for assign_id, assign_data in app_data["assignments"].items():
                if assign_data.get("module_id") == int(selected_module_id):
                    assignments.append(assign_data)
            
            blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"📊 Report for {module.get('name', 'Unknown Module')}"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Description:* {module.get('description', 'No description')}\n*Category:* {module.get('category', 'Unknown')}"
                    }
                }
            ]
            
            if assignments:
                blocks.append({"type": "divider"})
                for assignment in assignments:
                    # Get engineer name
                    engineer_name = "Unknown Engineer"
                    engineer_id = assignment.get("engineer_id")
                    if engineer_id:
                        for eng_id, eng_data in app_data["engineers"].items():
                            if int(eng_id) == engineer_id:
                                engineer_name = eng_data.get("name", "Unknown Engineer")
                                break
                    
                    blocks.append({
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"👤 *{engineer_name}*\nStatus: {assignment.get('status', 'Unknown').title()}\nDue: {assignment.get('due_date', 'No due date')}"
                        }
                    })
            else:
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "No assignments found for this module."
                    }
                })
            
            client.chat_postMessage(
                channel=body["user"]["id"],
                blocks=blocks
            )
            
        except Exception as e:
            print(f"Error generating module report: {e}")
            client.chat_postMessage(
                channel=body["user"]["id"],
                text="❌ Error generating report. Please try again."
            )

    @app.action("view_assessment_report")
    def handle_view_assessment_report(ack, body, client):
        ack()
        try:
            app_data = get_app_data()
            # Get selected assessment from the modal
            selected_assessment_id = None
            if body.get('view') and body['view'].get('state', {}).get('values'):
                values = body['view']['state']['values']
                if 'assessment_selection' in values and 'selected_assessment' in values['assessment_selection']:
                    selected_assessment_id = values['assessment_selection']['selected_assessment']['selected_option']['value']
            
            if not selected_assessment_id:
                client.chat_postMessage(
                    channel=body["user"]["id"],
                    text="❌ Please select an assessment first."
                )
                return
            
            # Get assessment details
            assessment = app_data["assessments"].get(selected_assessment_id)
            if not assessment:
                client.chat_postMessage(
                    channel=body["user"]["id"],
                    text="❌ Assessment not found."
                )
                return
            
            # Generate report for the assessment
            assignments = []
            for assign_id, assign_data in app_data["assignments"].items():
                if assign_data.get("module_id") == int(selected_assessment_id) and assign_data.get("type") == "assessment":
                    assignments.append(assign_data)
            
            blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"📊 Report for {assessment.get('name', 'Unknown Assessment')}"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Description:* {assessment.get('description', 'No description')}\n*Category:* {assessment.get('category', 'Unknown')}"
                    }
                }
            ]
            
            if assignments:
                blocks.append({"type": "divider"})
                for assignment in assignments:
                    # Get engineer name
                    engineer_name = "Unknown Engineer"
                    engineer_id = assignment.get("engineer_id")
                    if engineer_id:
                        for eng_id, eng_data in app_data["engineers"].items():
                            if int(eng_id) == engineer_id:
                                engineer_name = eng_data.get("name", "Unknown Engineer")
                                break
                    
                    blocks.append({
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"👤 *{engineer_name}*\nStatus: {assignment.get('status', 'Unknown').title()}\nDue: {assignment.get('due_date', 'No due date')}"
                        }
                    })
            else:
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "No assignments found for this assessment."
                    }
                })
            
            client.chat_postMessage(
                channel=body["user"]["id"],
                blocks=blocks
            )
            
        except Exception as e:
            print(f"Error generating assessment report: {e}")
            client.chat_postMessage(
                channel=body["user"]["id"],
                text="❌ Error generating report. Please try again."
            )

    # Configuration action handlers
    @app.action("create_module_button")
    def handle_create_module_button(ack, body, client):
        ack()
        try:
            from ui.module_modals import create_module_modal
            client.views_open(
                trigger_id=body["trigger_id"],
                view=create_module_modal()
            )
        except Exception as e:
            print(f"Error opening create module modal: {e}")

    @app.action("edit_module_button")
    def handle_edit_module_button(ack, body, client):
        ack()
        try:
            app_data = get_app_data()
            from ui.module_modals import create_module_selection_modal
            client.views_open(
                trigger_id=body["trigger_id"],
                view=create_module_selection_modal(app_data, "edit")
            )
        except Exception as e:
            print(f"Error opening edit module modal: {e}")

    @app.action("view_modules_button")
    def handle_view_modules_button(ack, body, client):
        ack()
        try:
            app_data = get_app_data()
            from ui.module_modals import create_modules_list_modal
            client.views_open(
                trigger_id=body["trigger_id"],
                view=create_modules_list_modal(app_data)
            )
        except Exception as e:
            print(f"Error opening modules list modal: {e}")

    @app.action("create_assessment_button")
    def handle_create_assessment_button(ack, body, client):
        ack()
        try:
            from ui.assessment_modals import create_assessment_modal
            client.views_open(
                trigger_id=body["trigger_id"],
                view=create_assessment_modal()
            )
        except Exception as e:
            print(f"Error opening create assessment modal: {e}")

    @app.action("edit_assessment_button")
    def handle_edit_assessment_button(ack, body, client):
        ack()
        try:
            app_data = get_app_data()
            from ui.assessment_modals import create_assessment_selection_modal
            client.views_open(
                trigger_id=body["trigger_id"],
                view=create_assessment_selection_modal(app_data, "edit")
            )
        except Exception as e:
            print(f"Error opening edit assessment modal: {e}")

    @app.action("view_assessments_button")
    def handle_view_assessments_button(ack, body, client):
        ack()
        try:
            app_data = get_app_data()
            from ui.assessment_modals import create_assessments_list_modal
            client.views_open(
                trigger_id=body["trigger_id"],
                view=create_assessments_list_modal(app_data)
            )
        except Exception as e:
            print(f"Error opening assessments list modal: {e}")

    @app.action("weekly_digest_settings")
    def handle_weekly_digest_settings(ack, body, client):
        ack()
        try:
            app_data = get_app_data()
            from ui.notification_modals import create_weekly_digest_modal
            client.views_open(
                trigger_id=body["trigger_id"],
                view=create_weekly_digest_modal(app_data)
            )
        except Exception as e:
            print(f"Error opening weekly digest settings modal: {e}")

    @app.action("reminder_settings")
    def handle_reminder_settings(ack, body, client):
        ack()
        try:
            app_data = get_app_data()
            from ui.notification_modals import create_reminder_settings_modal
            client.views_open(
                trigger_id=body["trigger_id"],
                view=create_reminder_settings_modal(app_data)
            )
        except Exception as e:
            print(f"Error opening reminder settings modal: {e}")

    @app.action("promote_to_manager")
    def handle_promote_to_manager(ack, body, client):
        ack()
        try:
            app_data = get_app_data()
            user_id = body["user"]["id"]
            
            # Find the user in engineers
            for eng_id, eng_data in app_data["engineers"].items():
                if eng_data.get("slack_user_id") == user_id:
                    # Update role to manager
                    eng_data["role"] = "manager"
                    eng_data["promoted_at"] = datetime.now().isoformat()
                    
                    # Save data
                    save_data(app_data)
                    
                    # Send confirmation
                    client.chat_postMessage(
                        channel=user_id,
                        text=f"🎉 Congratulations! You've been promoted to Manager role. You now have access to all configuration features!"
                    )
                    
                    # Update the configurations tab
                    from ui.configurations import create_configurations_view
                    client.views_publish(
                        user_id=user_id,
                        view=create_configurations_view(user_id, app_data)
                    )
                    return
            
            # If user not found in engineers
            client.chat_postMessage(
                channel=user_id,
                text="❌ User not found in the system. Please add yourself as an engineer first."
            )
            
        except Exception as e:
            print(f"Error promoting user to manager: {e}")
            client.chat_postMessage(
                channel=body["user"]["id"],
                text="❌ Error promoting to manager. Please try again."
            )
