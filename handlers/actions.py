from datetime import datetime
import json
import re
from engineer_tenures import get_team, get_geo, get_onboarding_plan, get_current_tenure, get_all_tenures


def _engineer_profile_lines(engineer):
    """Format team history (all tenures) for profile/report so report contains all teams."""
    lines = ["*Team history:*"]
    for t in get_all_tenures(engineer):
        team = t.get("team", "unassigned").replace("_", " ").title()
        geo = t.get("geo", "unassigned").replace("_", " ").title()
        plan = t.get("onboarding_plan", "custom").replace("_", " ").title()
        start = (t.get("start_date") or "")[:10] or "—"
        end = (t.get("end_date") or "")[:10] if t.get("end_date") else "Ongoing"
        lines.append(f"• {team} ({geo}) · {plan} · {start} → {end}")
    return "\n".join(lines) if len(lines) > 1 else "*Team history:* —"


def register_actions(app, get_app_data, save_data):
    """Register all action handlers"""
    
    @app.action("add_engineer_button")
    def handle_add_engineer_button(ack, body, client):
        ack()
        try:
            from auth import is_admin
            app_data = get_app_data()
            user_id = body["user"]["id"]
            
            # Authorization check
            if not is_admin(user_id, app_data):
                client.chat_postMessage(
                    channel=user_id,
                    text="❌ *Access Denied*\n\nYou don't have permission to add engineers. This feature is restricted to managers and administrators only."
                )
                return
            
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
            from auth import is_admin
            app_data = get_app_data()
            user_id = body["user"]["id"]
            
            # Authorization check
            if not is_admin(user_id, app_data):
                client.chat_postMessage(
                    channel=user_id,
                    text="❌ *Access Denied*\n\nYou don't have permission to assign modules. This feature is restricted to managers and administrators only."
                )
                return
            
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
            from auth import is_admin
            app_data = get_app_data()
            user_id = body["user"]["id"]
            
            # Authorization check
            if not is_admin(user_id, app_data):
                client.chat_postMessage(
                    channel=user_id,
                    text="❌ *Access Denied*\n\nYou don't have permission to assign assessments. This feature is restricted to managers and administrators only."
                )
                return
            
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
            from auth import is_admin
            app_data = get_app_data()
            user_id = body["user"]["id"]
            
            # Authorization check
            if not is_admin(user_id, app_data):
                client.chat_postMessage(
                    channel=user_id,
                    text="❌ *Access Denied*\n\nYou don't have permission to generate reports. This feature is restricted to managers and administrators only."
                )
                return
            
            from ui.modals import create_report_type_selection_modal
            client.views_open(
                trigger_id=body["trigger_id"],
                view=create_report_type_selection_modal()
            )
        except Exception as e:
            print(f"Error opening report type selection modal: {e}")

    @app.action("talent_profile_button")
    def handle_talent_profile_button(ack, body, client):
        ack()
        try:
            from auth import is_admin
            app_data = get_app_data()
            user_id = body.get("user", {}).get("id")
            if not is_admin(user_id, app_data):
                client.chat_postMessage(channel=user_id, text="❌ Only admins and managers can view Talent Profiles.")
                return
            from ui.modals import create_talent_profile_modal
            client.views_open(
                trigger_id=body["trigger_id"],
                view=create_talent_profile_modal(app_data)
            )
        except Exception as e:
            print(f"Error opening talent profile modal: {e}")
            if body.get("user", {}).get("id"):
                client.chat_postMessage(channel=body["user"]["id"], text="❌ Could not open Talent Profile. Try again.")

    @app.action("talent_profile_export_pdf")
    def handle_talent_profile_export_pdf(ack, body, client):
        ack()
        try:
            import os
            from datetime import datetime
            from pdf_generator import generate_engineer_report
            view = body.get("view", {})
            engineer_id = view.get("private_metadata")
            if not engineer_id:
                return
            app_data = get_app_data()
            engineer = app_data["engineers"].get(engineer_id)
            if not engineer:
                return
            assignments = [a for a in app_data["assignments"].values() if a.get("engineer_id") == int(engineer_id)]
            name = engineer.get("name", "Unknown").replace(" ", "_")
            filename = f"talent_profile_{name}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
            generate_engineer_report(engineer, assignments, app_data, filename)
            dm = client.conversations_open(users=[body["user"]["id"]])
            with open(filename, "rb") as f:
                client.files_upload_v2(
                    channel=dm["channel"]["id"],
                    file=f,
                    filename=filename,
                    title=f"Talent Profile: {engineer.get('name', 'Unknown')}",
                    initial_comment="📄 Talent Profile PDF (requested from popup)."
                )
            if os.path.exists(filename):
                os.remove(filename)
            # Update modal to show success
            client.views_update(
                view_id=view["id"],
                hash=view.get("hash"),
                view={
                    "type": "modal",
                    "callback_id": "talent_profile_display",
                    "title": {"type": "plain_text", "text": "Talent Profile"},
                    "close": {"type": "plain_text", "text": "Close"},
                    "private_metadata": engineer_id,
                    "blocks": [{"type": "section", "text": {"type": "mrkdwn", "text": "✅ *PDF exported.* Check your DM for the file.\nYou can close this window."}}]
                }
            )
        except Exception as e:
            print(f"Error exporting talent profile PDF: {e}")
            if body.get("user", {}).get("id"):
                client.chat_postMessage(channel=body["user"]["id"], text="❌ Could not generate PDF. Please try again.")

    @app.action("talent_profile_close")
    def handle_talent_profile_close(ack, body, client):
        ack()
        try:
            view = body.get("view", {})
            if not view.get("id"):
                return
            # Replace modal with a simple "close this window" view
            client.views_update(
                view_id=view["id"],
                hash=view.get("hash"),
                view={
                    "type": "modal",
                    "callback_id": "talent_profile_display",
                    "title": {"type": "plain_text", "text": "Talent Profile"},
                    "close": {"type": "plain_text", "text": "Close"},
                    "blocks": [{"type": "section", "text": {"type": "mrkdwn", "text": "You can close this window."}}]
                }
            )
        except Exception as e:
            print(f"Error closing talent profile: {e}")

    @app.action("set_end_date_button")
    def handle_set_end_date_button(ack, body, client):
        ack()
        try:
            from auth import is_admin
            app_data = get_app_data()
            user_id = body.get("user", {}).get("id")
            if not is_admin(user_id, app_data):
                client.chat_postMessage(channel=user_id, text="❌ Only admins can set end dates.")
                return
            initial_engineer_id = None
            if body.get("actions") and body["actions"][0].get("value"):
                initial_engineer_id = body["actions"][0]["value"]
            from ui.modals import create_set_end_date_modal
            client.views_open(
                trigger_id=body["trigger_id"],
                view=create_set_end_date_modal(app_data, initial_engineer_id=initial_engineer_id)
            )
        except Exception as e:
            print(f"Error opening set end date modal: {e}")
            if body.get("user", {}).get("id"):
                client.chat_postMessage(channel=body["user"]["id"], text="❌ Could not open Set end date. Try again.")

    @app.action("report_type_by_engineer")
    def handle_report_type_by_engineer(ack, body, client):
        ack()
        try:
            app_data = get_app_data()
            from ui.modals import create_engineer_report_modal
            
            # Use views.push to stack the new modal on top
            client.views_push(
                trigger_id=body["trigger_id"],
                view=create_engineer_report_modal(app_data)
            )
            print("✅ Pushed engineer report modal")
        except Exception as e:
            print(f"Error opening engineer report modal: {e}")
            import traceback
            traceback.print_exc()

    @app.action("report_type_by_module")
    def handle_report_type_by_module(ack, body, client):
        ack()
        try:
            app_data = get_app_data()
            from ui.modals import create_module_report_modal
            
            # Use views.push to stack the new modal on top
            client.views_push(
                trigger_id=body["trigger_id"],
                view=create_module_report_modal(app_data)
            )
            print("✅ Pushed module report modal")
        except Exception as e:
            print(f"Error opening module report modal: {e}")
            import traceback
            traceback.print_exc()

    @app.action("report_type_by_assessments")
    def handle_report_type_by_assessments(ack, body, client):
        ack()
        try:
            app_data = get_app_data()
            from ui.modals import create_assessment_report_modal
            
            # Use views.push to stack the new modal on top
            client.views_push(
                trigger_id=body["trigger_id"],
                view=create_assessment_report_modal(app_data)
            )
            print("✅ Pushed assessment report modal")
        except Exception as e:
            print(f"Error opening assessment report modal: {e}")
            import traceback
            traceback.print_exc()

    @app.action("report_type_due_report")
    def handle_report_type_due_report(ack, body, client):
        ack()
        try:
            from ui.modals import create_due_report_modal
            
            # Use views.push to stack the new modal on top
            client.views_push(
                trigger_id=body["trigger_id"],
                view=create_due_report_modal()
            )
            print("✅ Pushed due report modal")
        except Exception as e:
            print(f"Error opening due report modal: {e}")
            import traceback
            traceback.print_exc()

    @app.action("configurations_button")
    def handle_configurations_button(ack, body, client):
        ack()
        try:
            from auth import is_admin
            app_data = get_app_data()
            user_id = body["user"]["id"]
            
            # Authorization check
            if not is_admin(user_id, app_data):
                client.chat_postMessage(
                    channel=user_id,
                    text="❌ *Access Denied*\n\nYou don't have permission to access configurations. This feature is restricted to managers and administrators only."
                )
                return
            
            from ui.configurations import create_configurations_view
            client.views_publish(
                user_id=user_id,
                view=create_configurations_view(user_id, app_data)
            )
        except Exception as e:
            print(f"Error opening configurations tab: {e}")

    @app.action("back_to_home_button")
    def handle_back_to_home_button(ack, body, client):
        ack()
        try:
            app_data = get_app_data(force_reload=True)  # Force fresh data
            from ui.home import create_home_view
            client.views_publish(
                user_id=body["user"]["id"],
                view=create_home_view(body["user"]["id"], app_data)
            )
        except Exception as e:
            print(f"Error returning to home: {e}")

    @app.action("refresh_home_button")
    def handle_refresh_home_button(ack, body, client):
        """Refresh the home view with latest data from database"""
        ack()
        try:
            user_id = body["user"]["id"]
            # Force reload from database to get freshest data
            app_data = get_app_data(force_reload=True)
            from ui.home import create_home_view
            client.views_publish(
                user_id=user_id,
                view=create_home_view(user_id, app_data)
            )
            print(f"✅ Home view refreshed for user {user_id}")
        except Exception as e:
            print(f"Error refreshing home: {e}")
            import traceback
            traceback.print_exc()

    @app.action("select_engineer_progress")
    def handle_select_engineer_progress(ack, body, client):
        """Handle engineer selection from dropdown to show their progress"""
        ack()
        try:
            user_id = body["user"]["id"]
            selected_engineer_id = body["actions"][0]["selected_option"]["value"]
            
            # Get fresh data and update home view with selected engineer
            app_data = get_app_data(force_reload=True)
            from ui.home import create_home_view
            client.views_publish(
                user_id=user_id,
                view=create_home_view(user_id, app_data, selected_engineer_id=selected_engineer_id)
            )
            print(f"✅ Engineer {selected_engineer_id} selected for progress view by user {user_id}")
        except Exception as e:
            print(f"Error selecting engineer progress: {e}")
            import traceback
            traceback.print_exc()

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
            
            # Import the leaderboard modal creator
            from ui.modals import create_leaderboard_modal
            
            # Open modal instead of sending DM
            client.views_open(
                trigger_id=body["trigger_id"],
                view=create_leaderboard_modal(app_data)
            )
            
        except Exception as e:
            print(f"Error opening leaderboard modal: {e}")
            # Fallback: send error message
            client.chat_postMessage(
                channel=body["user"]["id"],
                text="❌ Error displaying leaderboard. Please try again."
            )

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
            
            # Check if it's a module assignment (legacy assignments may lack "type" field)
            if assignment.get("type") and assignment["type"] != "module":
                client.chat_postMessage(
                    channel=user_id,
                    text="❌ This is not a module assignment."
                )
                return
            
            # Look up module for trailhead_url
            mod_id = str(assignment.get("module_id", ""))
            module_record = app_data.get("modules", {}).get(mod_id, {})
            trailhead_url = module_record.get("trailhead_url") or ""

            # Open module start modal
            from ui.module_modal import create_module_start_modal
            client.views_open(
                trigger_id=body["trigger_id"],
                view=create_module_start_modal(
                    assignment.get("module_name") or module_record.get("name", "Unknown Module"),
                    assignment.get("module_description") or module_record.get("description", "No description"),
                    assignment.get("due_date", "No due date"),
                    assignment_id,
                    module_id=assignment.get("module_id"),
                    trailhead_url=trailhead_url
                )
            )
            
        except Exception as e:
            print(f"Error opening module: {e}")
            client.chat_postMessage(
                channel=body["user"]["id"],
                text="❌ Error opening module. Please try again."
            )

    @app.action(re.compile(r"acknowledge_module_\d+"))
    def handle_acknowledge_module(ack, body, client):
        """March Accreditation (and similar): Acknowledge button marks the module as completed."""
        ack()
        try:
            app_data = get_app_data()
            user_id = body["user"]["id"]
            action_id = body["actions"][0]["action_id"]
            assignment_id = action_id.split("_")[-1]
            assignment = app_data["assignments"].get(assignment_id)
            if not assignment:
                for assign_key, assign_data in app_data["assignments"].items():
                    if str(assign_data.get("id")) == assignment_id:
                        assignment = assign_data
                        assignment_id = assign_key
                        break
            if not assignment:
                client.chat_postMessage(channel=user_id, text="❌ Assignment not found.")
                return
            engineer = None
            for eng_id, eng_data in app_data["engineers"].items():
                if eng_data.get("slack_user_id") == user_id:
                    engineer = eng_data
                    engineer["id"] = eng_id
                    break
            if not engineer or int(engineer["id"]) != assignment.get("engineer_id"):
                client.chat_postMessage(channel=user_id, text="❌ You are not authorized to complete this assignment.")
                return
            assignment["status"] = "completed"
            assignment["completed_at"] = datetime.now().isoformat()
            progress_id = app_data["next_ids"]["progress"]
            app_data["next_ids"]["progress"] += 1
            app_data["progress"][str(progress_id)] = {
                "id": progress_id,
                "assignment_id": int(assignment.get("id", assignment_id)),
                "engineer_id": assignment["engineer_id"],
                "progress_percentage": 100,
                "completed_at": datetime.now().isoformat(),
                "type": "module"
            }
            save_data(app_data)
            module_name = assignment.get("module_name", "March Accreditation")
            client.chat_postMessage(
                channel=user_id,
                text=f"✅ *March Accreditation* acknowledged and marked as completed!",
                blocks=[
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"✅ *Module completed*\n\n📚 *{module_name}* acknowledged and marked complete."
                        }
                    }
                ]
            )
            from ui.home import create_home_view
            try:
                client.views_publish(user_id=user_id, view=create_home_view(user_id, app_data))
            except Exception:
                pass
        except Exception as e:
            print(f"Error acknowledging module: {e}")
            if body.get("user", {}).get("id"):
                client.chat_postMessage(channel=body["user"]["id"], text="❌ Could not complete. Please try again.")

    @app.action(re.compile(r"complete_module_\d+"))
    def handle_complete_module(ack, body, client):
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
                        assignment_id = assign_key
                        break
                
                if not assignment:
                    client.chat_postMessage(
                        channel=user_id,
                        text="❌ Assignment not found."
                    )
                    return
            
            # Verify user is the assigned engineer
            engineer = None
            for eng_id, eng_data in app_data["engineers"].items():
                if eng_data.get("slack_user_id") == user_id:
                    engineer = eng_data
                    engineer["id"] = eng_id
                    break
            
            if not engineer or int(engineer["id"]) != assignment.get("engineer_id"):
                client.chat_postMessage(
                    channel=user_id,
                    text="❌ You are not authorized to complete this assignment."
                )
                return
            
            # Update assignment status
            assignment["status"] = "completed"
            assignment["completed_at"] = datetime.now().isoformat()
            
            # Save progress
            progress_id = app_data["next_ids"]["progress"]
            app_data["next_ids"]["progress"] += 1
            
            app_data["progress"][str(progress_id)] = {
                "id": progress_id,
                "assignment_id": int(assignment.get("id", assignment_id)),
                "engineer_id": assignment["engineer_id"],
                "progress_percentage": 100,
                "completed_at": datetime.now().isoformat(),
                "type": assignment.get("type", "module")
            }
            
            # Check if we should unlock the next module
            current_order = assignment.get("sequence_order", 0)
            if current_order > 0:
                # Find next module in sequence
                for other_assign_id, other_assign in app_data["assignments"].items():
                    if (other_assign.get("engineer_id") == assignment["engineer_id"] and 
                        other_assign.get("sequence_order") == current_order + 1 and
                        other_assign.get("status") == "locked"):
                        # Unlock next module
                        other_assign["status"] = "assigned"
                        other_assign["unlocked"] = True
                        other_assign["locked_reason"] = None
                        
                        # Notify about unlocked module
                        client.chat_postMessage(
                            channel=user_id,
                            text=f"🎉 Great job! You've unlocked the next module: *{other_assign.get('module_name', 'Next Module')}*"
                        )
                        break
            
            save_data(app_data)
            
            # Send confirmation message with updated status
            module_name = assignment.get("module_name", assignment.get("module_id", "Unknown Module"))
            client.chat_postMessage(
                channel=user_id,
                text=f"✅ Congratulations! Module '*{module_name}*' marked as completed!",
                blocks=[
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"✅ *Module Completed!*\n\n"
                                   f"📚 *Module:* {module_name}\n"
                                   f"🗓️ *Completed:* {datetime.now().strftime('%B %d, %Y at %I:%M %p')}\n"
                                   f"🎯 *Status:* Completed"
                        }
                    }
                ]
            )
            
            # Update home view
            from ui.home import create_home_view
            client.views_publish(
                user_id=user_id,
                view=create_home_view(user_id, app_data)
            )
            
        except Exception as e:
            print(f"Error completing module: {e}")
            import traceback
            traceback.print_exc()
            client.chat_postMessage(
                channel=body["user"]["id"],
                text="❌ Error completing module. Please try again."
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

    # Assessment modal interaction handlers
    @app.action(re.compile(r"question_\d+_answer"))
    def handle_question_answer_selection(ack, body, logger):
        """Handle radio button selections in assessment modal"""
        ack()
        # Just acknowledge - the actual answer processing happens on submit
        logger.info(f"Question answer selected: {body['actions'][0]['action_id']}")

    # Modal form element handlers (acknowledge but don't process until submit)
    @app.action("acknowledge_completion")
    def handle_acknowledge_completion_checkbox(ack, body, logger):
        """Handle completion acknowledgment checkbox in module modal"""
        ack()
        logger.info("Completion checkbox toggled")

    @app.action("status_select")
    def handle_status_select_dropdown(ack, body, logger):
        """Handle status filter dropdown in report modals"""
        ack()
        logger.info("Status filter selected")

    @app.action("report_type_select")
    def handle_report_type_select_dropdown(ack, body, logger):
        """Handle report type dropdown (if used)"""
        ack()
        logger.info("Report type selected")

    # Engineer ping and acknowledgment handlers
    @app.action(re.compile(r"ping_engineer_\d+"))
    def handle_ping_engineer(ack, body, client):
        """Handle ping button to send reminder to engineer"""
        ack()
        try:
            from datetime import datetime
            from auth import is_admin
            
            app_data = get_app_data()
            user_id = body["user"]["id"]
            
            # Authorization check
            if not is_admin(user_id, app_data):
                client.chat_postMessage(
                    channel=user_id,
                    text="❌ *Access Denied*\n\nYou don't have permission to ping engineers."
                )
                return
            
            # Extract engineer ID from action_id
            action_id = body["actions"][0]["action_id"]
            engineer_id = action_id.split("_")[-1]
            
            # Get engineer data
            engineer = app_data["engineers"].get(engineer_id)
            if not engineer:
                client.chat_postMessage(
                    channel=user_id,
                    text="❌ Engineer not found."
                )
                return
            
            engineer_slack_id = engineer.get("slack_user_id")
            engineer_name = engineer.get("name", "Unknown")
            
            # Get incomplete assignments for this engineer
            incomplete_assignments = []
            for assign_id, assign_data in app_data["assignments"].items():
                if assign_data.get("engineer_id") == int(engineer_id) and assign_data.get("status") != "completed":
                    incomplete_assignments.append(assign_data)
            
            # Build reminder message
            assignment_list = []
            for i, assign in enumerate(incomplete_assignments[:5], 1):  # Limit to 5
                module_name = assign.get("module_name", "Unknown Module")
                due_date = assign.get("due_date", "No due date")
                status = assign.get("status", "assigned").title()
                assignment_list.append(f"{i}. *{module_name}* - Due: {due_date} - Status: {status}")
            
            assignments_text = "\n".join(assignment_list)
            if len(incomplete_assignments) > 5:
                assignments_text += f"\n\n_...and {len(incomplete_assignments) - 5} more assignments_"
            
            # Store ping status
            if "ping_acknowledgments" not in app_data:
                app_data["ping_acknowledgments"] = {}
            
            app_data["ping_acknowledgments"][f"engineer_{engineer_id}"] = {
                "status": "pending",
                "timestamp": datetime.now().isoformat(),
                "sent_by": user_id
            }
            save_data(app_data)
            
            # Send DM to engineer with acknowledge button
            client.chat_postMessage(
                channel=engineer_slack_id,
                text=f"👋 Hi {engineer_name}! This is a friendly reminder about your pending assignments.",
                blocks=[
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": "📍 Assignment Reminder"
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"Hi *{engineer_name}*! 👋\n\nYou have *{len(incomplete_assignments)} incomplete assignment(s)*. Please review and complete them at your earliest convenience."
                        }
                    },
                    {
                        "type": "divider"
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*📋 Pending Assignments:*\n\n{assignments_text}"
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "💡 *Need help?* Reach out to your manager or check the Home tab for more details."
                        }
                    },
                    {
                        "type": "actions",
                        "elements": [
                            {
                                "type": "button",
                                "text": {
                                    "type": "plain_text",
                                    "text": "✅ I Acknowledge This Reminder"
                                },
                                "action_id": f"acknowledge_ping_{engineer_id}",
                                "style": "primary"
                            }
                        ]
                    }
                ]
            )
            
            # Confirm to admin
            client.chat_postMessage(
                channel=user_id,
                text=f"✅ Reminder sent to *{engineer_name}* about {len(incomplete_assignments)} incomplete assignment(s)."
            )
            
            # Update home view for admin with fresh data
            from ui.home import create_home_view
            fresh_data = get_app_data(force_reload=True)  # Force reload to show ping status
            client.views_publish(
                user_id=user_id,
                view=create_home_view(user_id, fresh_data)
            )
            
            print(f"✅ Ping sent to engineer {engineer_name} by {user_id}")
            
        except Exception as e:
            print(f"Error sending ping: {e}")
            import traceback
            traceback.print_exc()
            client.chat_postMessage(
                channel=body["user"]["id"],
                text=f"❌ Error sending reminder: {str(e)}"
            )

    @app.action(re.compile(r"acknowledge_ping_\d+"))
    def handle_acknowledge_ping(ack, body, client):
        """Handle engineer acknowledging the ping reminder"""
        ack()
        try:
            from datetime import datetime
            
            app_data = get_app_data()
            user_id = body["user"]["id"]
            
            # Extract engineer ID from action_id
            action_id = body["actions"][0]["action_id"]
            engineer_id = action_id.split("_")[-1]
            
            # Verify this is the correct engineer
            engineer = app_data["engineers"].get(engineer_id)
            if not engineer or engineer.get("slack_user_id") != user_id:
                client.chat_postMessage(
                    channel=user_id,
                    text="❌ Error: Unable to verify your identity."
                )
                return
            
            engineer_name = engineer.get("name", "Unknown")
            
            # Update acknowledgment status
            if "ping_acknowledgments" not in app_data:
                app_data["ping_acknowledgments"] = {}
            
            ping_data = app_data["ping_acknowledgments"].get(f"engineer_{engineer_id}", {})
            sent_by = ping_data.get("sent_by", "")
            
            app_data["ping_acknowledgments"][f"engineer_{engineer_id}"] = {
                "status": "acknowledged",
                "timestamp": datetime.now().isoformat(),
                "acknowledged_at": datetime.now().isoformat(),
                "sent_by": sent_by
            }
            save_data(app_data)
            
            # Confirm to engineer
            client.chat_postMessage(
                channel=user_id,
                text=f"✅ Thank you for acknowledging! Your manager has been notified that you've seen this reminder."
            )
            
            # Notify the manager who sent the ping
            if sent_by:
                try:
                    client.chat_postMessage(
                        channel=sent_by,
                        text=f"🔔 *{engineer_name}* has acknowledged your reminder!"
                    )
                    
                    # Update manager's home view with fresh data
                    from ui.home import create_home_view
                    manager_data = get_app_data(force_reload=True)  # Force reload to show acknowledgment
                    client.views_publish(
                        user_id=sent_by,
                        view=create_home_view(sent_by, manager_data)
                    )
                    print(f"✅ Manager {sent_by} home view updated with acknowledgment")
                except Exception as e:
                    print(f"Could not notify manager: {e}")
            
            print(f"✅ Ping acknowledged by engineer {engineer_name}")
            
        except Exception as e:
            print(f"Error acknowledging ping: {e}")
            import traceback
            traceback.print_exc()
            client.chat_postMessage(
                channel=body["user"]["id"],
                text=f"❌ Error processing acknowledgment: {str(e)}"
            )

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
                        "text": _engineer_profile_lines(engineer)
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
    
    @app.action("open_search_modal")
    def handle_open_search_modal(ack, body, client):
        """Open the search modal"""
        ack()
        try:
            from ui.search_modal import create_search_modal
            client.views_open(
                trigger_id=body["trigger_id"],
                view=create_search_modal()
            )
            print("✅ Opened search modal")
        except Exception as e:
            print(f"Error opening search modal: {e}")
            import traceback
            traceback.print_exc()

    # URL-opening buttons: Slack still sends an action event, so just ack them.
    for action_id in ("open_trailhead_profile", "open_trailhead_module", "open_learning_materials"):
        app.action(action_id)(lambda ack, **kwargs: ack())
