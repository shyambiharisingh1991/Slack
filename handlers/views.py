from datetime import datetime, timedelta
import json

def migrate_existing_assignments(app_data, save_data):
    """Migrate existing assignments to include locking system"""
    updated = False
    
    # Group assignments by engineer
    engineer_assignments = {}
    for assign_id, assign_data in app_data["assignments"].items():
        engineer_id = assign_data.get("engineer_id")
        if engineer_id not in engineer_assignments:
            engineer_assignments[engineer_id] = []
        engineer_assignments[engineer_id].append((assign_id, assign_data))
    
    # Process each engineer's assignments
    for engineer_id, assignments in engineer_assignments.items():
        # Check if any assignment needs migration
        needs_migration = any("sequence_order" not in assign_data for _, assign_data in assignments)
        
        if needs_migration:
            print(f"Migrating assignments for engineer {engineer_id}")
            
            # Sort by assignment ID to maintain order
            assignments.sort(key=lambda x: int(x[1].get("id", 0)))
            
            # Update each assignment with sequence order and locking
            for i, (assign_id_key, assign_data_item) in enumerate(assignments):
                assign_data_item["sequence_order"] = i + 1
                assign_data_item["unlocked"] = i == 0
                
                if i == 0:
                    # First module - should be unlocked
                    if assign_data_item.get("status") in ["assigned", "in_progress"]:
                        assign_data_item["status"] = "in_progress"
                else:
                    # Subsequent modules - should be locked
                    assign_data_item["status"] = "locked"
                    assign_data_item["locked_reason"] = "Complete previous module to unlock"
                
                print(f"  Assignment {assign_data_item['id']}: sequence_order={i+1}, status={assign_data_item['status']}")
                updated = True
    
    if updated:
        save_data(app_data)
        print("Migration completed - existing assignments updated with locking system")
    else:
        print("No migration needed - all assignments already have locking system")

def register_views(app, get_app_data, save_data):
    """Register all view handlers"""
    from engineer_tenures import migrate_engineers_to_tenures
    # Migrate existing assignments on startup
    app_data = get_app_data()
    migrate_existing_assignments(app_data, save_data)
    if migrate_engineers_to_tenures(app_data):
        save_data(app_data)
    
    @app.view("add_engineer_modal")
    def handle_add_engineer_submission(ack, body, client, view):
        ack()
        
        try:
            app_data = get_app_data()
            # Extract form data
            values = view["state"]["values"]
            slack_user_id = values["engineer_slack_user"]["slack_user_select"]["selected_user"]
            team = values["engineer_team"]["team_select"]["selected_option"]["value"]
            geo = values["engineer_geo"]["geo_select"]["selected_option"]["value"]
            onboarding_plan = values["onboarding_plan"]["plan_select"]["selected_option"]["value"]
            start_date_str = values["start_date"]["start_date_picker"]["selected_date"]
            trailhead_username = (values.get("trailhead_username", {}).get("trailhead_input", {}).get("value") or "").strip()
            
            # Get user info from Slack (email requires users:read.email scope)
            user_info = client.users_info(user=slack_user_id)
            name = user_info["user"]["real_name"] or user_info["user"]["name"]
            email = (user_info["user"].get("profile") or {}).get("email", "") or ""
            
            # Find existing engineer (one profile per person) or create new
            from engineer_tenures import add_tenure, get_team, get_geo, get_onboarding_plan
            existing_engineer = None
            existing_eng_id = None
            for eng_id, eng_data in app_data["engineers"].items():
                if eng_data.get("slack_user_id") == slack_user_id:
                    existing_engineer = eng_data
                    existing_eng_id = eng_id
                    break
            
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
            if existing_engineer:
                # Same person, new team stint: add a tenure (end previous) and create assignments
                engineer_id = int(existing_eng_id)
                add_tenure(existing_engineer, team, geo, onboarding_plan, start_date_str)
                if email:
                    existing_engineer["email"] = email
                if name:
                    existing_engineer["name"] = name
                if trailhead_username:
                    existing_engineer["trailhead_username"] = trailhead_username
            else:
                # New person: create engineer profile with first tenure
                engineer_id = app_data["next_ids"]["engineers"]
                app_data["next_ids"]["engineers"] += 1
                new_engineer = {
                    "id": engineer_id,
                    "name": name,
                    "email": email,
                    "slack_user_id": slack_user_id,
                    "role": "engineer",
                    "created_at": datetime.now().isoformat(),
                    "trailhead_username": trailhead_username,
                    "tenures": [
                        {
                            "team": team,
                            "geo": geo,
                            "onboarding_plan": onboarding_plan,
                            "start_date": start_date_str,
                            "end_date": None,
                        }
                    ],
                }
                app_data["engineers"][str(engineer_id)] = new_engineer
            
            # Create assignments for this stint (same for new or existing engineer)
            
            # Create 3 sample assignments with calculated due dates
            modules_data = [
                {"name": f"Introduction to {team.replace('_', ' ').title()}", "days_offset": 5},
                {"name": "Architecture Overview", "days_offset": 10}, 
                {"name": "API Development Basics", "days_offset": 15}
            ]
            
            assignments = []
            for i, module_data in enumerate(modules_data):
                # Create or get module
                module = None
                for mod_id, mod_data in app_data["modules"].items():
                    if mod_data.get("name") == module_data["name"]:
                        module = mod_data
                        module["id"] = mod_id
                        break
                
                if not module:
                    module_id = app_data["next_ids"]["modules"]
                    app_data["next_ids"]["modules"] += 1
                    
                    module = {
                        "id": module_id,
                        "name": module_data["name"],
                        "description": f"Essential training for {team.replace('_', ' ').title()} team",
                        "category": "basics",
                        "created_at": datetime.now().isoformat()
                    }
                    app_data["modules"][str(module_id)] = module
                
                # Create assignment with all date fields
                assignment_id = app_data["next_ids"]["assignments"]
                app_data["next_ids"]["assignments"] += 1
                
                assignment = {
                    "id": assignment_id,
                    "engineer_id": engineer_id,
                    "module_id": module["id"],
                    "assigned_by": body["user"]["id"],
                    "assigned_at": datetime.now().isoformat(),
                    "start_date": (start_date + timedelta(days=module_data["days_offset"] - 5)).isoformat(),
                    "due_date": (start_date + timedelta(days=module_data["days_offset"])).isoformat(),
                    "status": "in_progress" if i == 0 else "locked",
                    "sequence_order": i + 1,  # Track the order (1, 2, 3, etc.)
                    "unlocked": i == 0,  # Only first module is unlocked
                    "locked_reason": "Complete previous module to unlock" if i > 0 else None
                }
                app_data["assignments"][str(assignment_id)] = assignment
                assignments.append(assignment)
            
            save_data(app_data)
            
            # Send welcome DM to the new engineer
            team_display = {
                'support': 'Support',
                'guides': 'Guides', 
                'success_architects': 'Success Architects',
                'fde': 'FDE'
            }
            
            plan_display = {
                'sales_signature': 'Sales Signature',
                'service_signature': 'Service - Signature',
                'service_premier': 'Service Premier',
                'prom': 'ProM',
                'guides': 'Guides',
                'success_architect': 'Success Architect'
            }
            
            # Get manager info (person who added the engineer)
            manager_info = client.users_info(user=body["user"]["id"])
            manager_name = manager_info["user"]["real_name"] or manager_info["user"]["name"]
            
            welcome_message = {
                "channel": slack_user_id,
                "blocks": [
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": "👋 Welcome to Engineering Onboarding!"
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"Hi {name}! 👋\n\n"
                                   f"Welcome to the {team_display.get(team, team.title())} team! "
                                   f"Your manager {manager_name} has set up your onboarding journey with the "
                                   f"{plan_display.get(onboarding_plan, onboarding_plan)} plan.\n\n"
                                   f"📅 **Start Date:** {start_date.strftime('%B %d, %Y')}\n"
                                   f"🏢 **Team:** {team_display.get(team, team.title())}\n"
                                   f"🌍 **Location:** {geo.title()}\n\n"
                                   f"You have been assigned {len(assignments)} training modules to complete. "
                                   f"Let's get started! 🚀"
                        }
                    },
                    {
                        "type": "divider"
                    }
                ]
            }
            
            # Add assignment blocks
            for i, assignment in enumerate(assignments, 1):
                module_name = app_data["modules"][str(assignment["module_id"])]["name"]
                due_date = datetime.fromisoformat(assignment["due_date"]).strftime('%B %d, %Y')
                
                # Check if module is locked
                is_locked = assignment.get("status") == "locked"
                button_text = "🔒 Locked" if is_locked else "Start Module"
                button_style = "danger" if is_locked else "primary"
                
                welcome_message["blocks"].extend([
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"📚 **Module {i}: {module_name}**\n"
                                   f"📅 Due: {due_date}\n"
                                   f"📊 Status: {assignment['status'].title()}"
                        },
                        "accessory": {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": button_text
                            },
                            "action_id": f"start_module_{assignment['id']}" if not is_locked else "locked_module",
                            "style": button_style
                        }
                    }
                ])
            
            client.chat_postMessage(**welcome_message)
            
            # Invite engineer to the engineer-onboarding channel
            ONBOARDING_CHANNEL_ID = "C09PL7HN3DZ"
            try:
                client.conversations_invite(
                    channel=ONBOARDING_CHANNEL_ID,
                    users=[slack_user_id]
                )
                print(f"✅ Added {name} to #engineer-onboarding channel")
                channel_added_message = " and added to #engineer-onboarding channel"
            except Exception as channel_error:
                # Log error but don't fail the entire process
                print(f"⚠️ Could not add {name} to #engineer-onboarding channel: {channel_error}")
                channel_added_message = ""
            
            # Send confirmation to manager
            client.chat_postMessage(
                channel=body["user"]["id"],
                text=f"✅ Successfully added engineer: {name} to {team_display.get(team, team.title())} team with {plan_display.get(onboarding_plan, onboarding_plan)} onboarding plan. Welcome message sent{channel_added_message}!"
            )
            
            # Save the data
            save_data(app_data)
            
            # Update home tab
            from ui.home import create_home_view
            client.views_publish(
                user_id=body["user"]["id"],
                view=create_home_view(body["user"]["id"], app_data)
            )
            
        except Exception as e:
            print(f"Error adding engineer: {e}")
            client.chat_postMessage(
                channel=body["user"]["id"],
                text="❌ Error adding engineer. Please try again."
            )

    @app.view("assign_module_modal")
    def handle_assign_module_submission(ack, body, client, view):
        try:
            # Extract form data for validation
            values = view["state"]["values"]
            due_date_str = values["due_date"]["due_date_picker"]["selected_date"]
            
            # Validate due date BEFORE acknowledging (cannot be in the past)
            from datetime import datetime as dt, date
            try:
                due_date_obj = dt.strptime(due_date_str, "%Y-%m-%d").date()
                today = date.today()
                if due_date_obj < today:
                    # Pass error to ack() to show in modal
                    ack(response_action="errors", errors={
                        "due_date": "❌ Due date cannot be in the past. Please select today or a future date."
                    })
                    return
            except ValueError:
                ack(response_action="errors", errors={
                    "due_date": "❌ Invalid date format. Please try again."
                })
                return
            
            # Validation passed - acknowledge the submission
            ack()
            
            app_data = get_app_data()
            engineer_id = values["engineer_selection"]["engineer_select"]["selected_user"]
            
            # Check if module was selected
            module_option = values["module_selection"]["module_select"].get("selected_option")
            if not module_option:
                client.chat_postMessage(
                    channel=body["user"]["id"],
                    text="❌ Please select a module."
                )
                return
            
            module_value = module_option["value"]
            
            # Get or create user info (allow any Slack user)
            engineer = None
            for eng_id, eng_data in app_data["engineers"].items():
                if eng_data.get("slack_user_id") == engineer_id:
                    engineer = eng_data
                    engineer["id"] = eng_id
                    break
            
            # If user not found in engineers, create a basic user record
            if not engineer:
                # Get user info from Slack (name + email for reports)
                try:
                    user_info = client.users_info(user=engineer_id)
                    user_name = user_info["user"]["real_name"] or user_info["user"]["display_name"] or "Unknown User"
                    user_email = user_info["user"].get("profile", {}).get("email", "") or ""
                except Exception:
                    user_name = "Unknown User"
                    user_email = ""
                
                # Create basic engineer record
                engineer_id_new = app_data["next_ids"]["engineers"]
                app_data["next_ids"]["engineers"] += 1
                
                engineer = {
                    "id": engineer_id_new,
                    "name": user_name,
                    "email": user_email,
                    "slack_user_id": engineer_id,
                    "role": "engineer",
                    "created_at": datetime.now().isoformat(),
                    "tenures": [{"team": "unassigned", "geo": "unassigned", "onboarding_plan": "custom", "start_date": datetime.now().date().isoformat(), "end_date": None}],
                }
                app_data["engineers"][str(engineer_id_new)] = engineer
                engineer["id"] = engineer_id_new
                # Invite to onboarding channel (auto-created engineer)
                ONBOARDING_CHANNEL_ID = "C09PL7HN3DZ"
                try:
                    client.conversations_invite(
                        channel=ONBOARDING_CHANNEL_ID,
                        users=[engineer_id]
                    )
                    print(f"✅ Added {user_name} to #engineer-onboarding channel (auto-created)")
                except Exception as channel_error:
                    print(f"⚠️ Could not add {user_name} to #engineer-onboarding: {channel_error}")
            
            # Handle predefined modules
            predefined_modules = [
                {"name": "Agentforce", "duration": 3, "description": "Learn Salesforce Agentforce platform"},
                {"name": "Data Cloud", "duration": 5, "description": "Master Salesforce Data Cloud capabilities"},
                {"name": "Apex", "duration": 7, "description": "Develop with Salesforce Apex programming"},
                {"name": "Integration", "duration": 4, "description": "Build integrations with Salesforce APIs"},
                {"name": "Message Queue", "duration": 3, "description": "Implement message queuing solutions"},
                {"name": "Deployments", "duration": 2, "description": "Deploy applications using CI/CD"},
                {"name": "March Accreditation", "duration": 0, "description": "Watch the video and review upcoming changes in March. Acknowledge to complete."},
            ]
            
            if module_value.startswith("predefined_"):
                module_index = int(module_value.split("_")[1])
                if 0 <= module_index < len(predefined_modules):
                    module = predefined_modules[module_index]
                else:
                    client.chat_postMessage(
                        channel=body["user"]["id"],
                        text="❌ Invalid module selection."
                    )
                    return
            else:
                # Handle custom modules from app_data
                module = app_data["modules"].get(module_value)
                if not module:
                    client.chat_postMessage(
                        channel=body["user"]["id"],
                        text="❌ Module not found."
                    )
                    return
            
            # Create assignment
            assignment_id = app_data["next_ids"]["assignments"]
            app_data["next_ids"]["assignments"] += 1
            
            assignment = {
                "id": assignment_id,
                "engineer_id": int(engineer["id"]),
                "module_id": module_value,  # Store the module identifier
                "module_name": module["name"],
                "module_description": module["description"],
                "assigned_by": body["user"]["id"],
                "assigned_at": datetime.now().isoformat(),
                "due_date": due_date_str,
                "status": "assigned",
                "type": "module"
            }
            app_data["assignments"][str(assignment_id)] = assignment
            
            save_data(app_data)
            
            # Send confirmation to manager
            client.chat_postMessage(
                channel=body["user"]["id"],
                text=f"✅ Successfully assigned {module['name']} to {engineer['name']} with due date {due_date_str}."
            )
            
            # Send notification to engineer with Start Module button
            blocks = [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"📚 *New module assignment: {module['name']}*\n📅 Due: {due_date_str}\n\nClick the button below to start the module:"
                    },
                    "accessory": {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "📚 Start Module"
                        },
                        "action_id": f"start_module_{assignment_id}",
                        "style": "primary"
                    }
                }
            ]
            
            client.chat_postMessage(
                channel=engineer_id,
                blocks=blocks
            )
            
            # Update home tab
            from ui.home import create_home_view
            client.views_publish(
                user_id=body["user"]["id"],
                view=create_home_view(body["user"]["id"], app_data)
            )
            
        except Exception as e:
            print(f"Error assigning module: {e}")
            client.chat_postMessage(
                channel=body["user"]["id"],
                text="❌ Error assigning module. Please try again."
            )

    @app.view("assign_assessment_modal")
    def handle_assign_assessment_submission(ack, body, client, view):
        try:
            # Extract form data for validation
            values = view["state"]["values"]
            due_date_str = values["due_date"]["due_date_picker"]["selected_date"]
            
            # Validate due date BEFORE acknowledging (cannot be in the past)
            from datetime import datetime as dt, date
            try:
                due_date_obj = dt.strptime(due_date_str, "%Y-%m-%d").date()
                today = date.today()
                if due_date_obj < today:
                    # Pass error to ack() to show in modal
                    ack(response_action="errors", errors={
                        "due_date": "❌ Due date cannot be in the past. Please select today or a future date."
                    })
                    return
            except ValueError:
                ack(response_action="errors", errors={
                    "due_date": "❌ Invalid date format. Please try again."
                })
                return
            
            # Validation passed - acknowledge the submission
            ack()
            
            app_data = get_app_data()
            engineer_id = values["engineer_selection"]["engineer_select"]["selected_user"]
            
            # Check if assessment was selected
            assessment_option = values["assessment_selection"]["assessment_select"].get("selected_option")
            if not assessment_option:
                client.chat_postMessage(
                    channel=body["user"]["id"],
                    text="❌ Please select an assessment."
                )
                return
            
            assessment_value = assessment_option["value"]
            
            # Get or create user info (allow any Slack user)
            engineer = None
            for eng_id, eng_data in app_data["engineers"].items():
                if eng_data.get("slack_user_id") == engineer_id:
                    engineer = eng_data
                    engineer["id"] = eng_id
                    break
            
            # If user not found in engineers, create a basic user record
            if not engineer:
                # Get user info from Slack (name + email for reports)
                try:
                    user_info = client.users_info(user=engineer_id)
                    user_name = user_info["user"]["real_name"] or user_info["user"]["display_name"] or "Unknown User"
                    user_email = user_info["user"].get("profile", {}).get("email", "") or ""
                except Exception:
                    user_name = "Unknown User"
                    user_email = ""
                
                # Create basic engineer record
                engineer_id_new = app_data["next_ids"]["engineers"]
                app_data["next_ids"]["engineers"] += 1
                
                engineer = {
                    "id": engineer_id_new,
                    "name": user_name,
                    "email": user_email,
                    "slack_user_id": engineer_id,
                    "role": "engineer",
                    "created_at": datetime.now().isoformat(),
                    "tenures": [{"team": "unassigned", "geo": "unassigned", "onboarding_plan": "custom", "start_date": datetime.now().date().isoformat(), "end_date": None}],
                }
                app_data["engineers"][str(engineer_id_new)] = engineer
                engineer["id"] = engineer_id_new
                # Invite to onboarding channel (auto-created engineer for assessment)
                ONBOARDING_CHANNEL_ID = "C09PL7HN3DZ"
                try:
                    client.conversations_invite(
                        channel=ONBOARDING_CHANNEL_ID,
                        users=[engineer_id]
                    )
                    print(f"✅ Added {user_name} to #engineer-onboarding channel (auto-created for assessment)")
                except Exception as channel_error:
                    print(f"⚠️ Could not add {user_name} to #engineer-onboarding: {channel_error}")
            
            # Get assessment by ID
            assessment = app_data["assessments"].get(assessment_value)
            if not assessment:
                client.chat_postMessage(
                    channel=body["user"]["id"],
                    text="❌ Assessment not found."
                )
                return
            
            # Create assignment
            assignment_id = app_data["next_ids"]["assignments"]
            app_data["next_ids"]["assignments"] += 1
            
            assignment = {
                "id": assignment_id,
                "engineer_id": int(engineer["id"]),
                "module_id": assessment["id"],  # Using module_id field for assessments too
                "assigned_by": body["user"]["id"],
                "assigned_at": datetime.now().isoformat(),
                "due_date": due_date_str,
                "status": "assigned",
                "type": "assessment"
            }
            app_data["assignments"][str(assignment_id)] = assignment
            
            # Debug logging
            print(f"Created assessment assignment with ID: {assignment_id}")
            print(f"Assignment data: {assignment}")
            print(f"Assignments dict keys: {list(app_data['assignments'].keys())}")
            print(f"Button action_id will be: start_assessment_{str(assignment_id)}")
            
            save_data(app_data)
            
            # Send confirmation to manager
            client.chat_postMessage(
                channel=body["user"]["id"],
                text=f"✅ Successfully assigned {assessment['name']} assessment to {engineer['name']} with due date {due_date_str}."
            )
            
            # Send notification to engineer with Start Assessment button
            blocks = [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"📋 *New assessment: {assessment['name']}*\n📅 Due: {due_date_str}\n\nClick the button below to start the assessment:"
                    },
                    "accessory": {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "📋 Start Assessment"
                        },
                        "action_id": f"start_assessment_{str(assignment_id)}",
                        "style": "primary"
                    }
                }
            ]
            
            client.chat_postMessage(
                channel=engineer_id,
                blocks=blocks
            )
            
            # Update home tab
            from ui.home import create_home_view
            client.views_publish(
                user_id=body["user"]["id"],
                view=create_home_view(body["user"]["id"], app_data)
            )
            
        except Exception as e:
            print(f"Error assigning assessment: {e}")
            client.chat_postMessage(
                channel=body["user"]["id"],
                text="❌ Error assigning assessment. Please try again."
            )

    @app.view("progress_update_modal")
    def handle_progress_update_submission(ack, body, client, view):
        ack()
        
        try:
            app_data = get_app_data()
            # Extract form data
            values = view["state"]["values"]
            progress_percentage = int(values["progress_percentage"]["progress_select"]["selected_option"]["value"])
            notes = values.get("notes", {}).get("notes_input", {}).get("value", "")
            assignment_id = view["private_metadata"]
            
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
            
            # Get module name
            module_name = "Unknown Module"
            module_id = assignment.get("module_id")
            if module_id and str(module_id) in app_data["modules"]:
                module_name = app_data["modules"][str(module_id)].get("name", "Unknown Module")
            
            # Create or update progress record
            progress_id = None
            for prog_id, prog_data in app_data["progress"].items():
                if prog_data.get("assignment_id") == int(assignment_id):
                    progress_id = prog_id
                    break
            
            if not progress_id:
                progress_id = app_data["next_ids"]["progress"]
                app_data["next_ids"]["progress"] += 1
            
            progress_record = {
                "id": progress_id,
                "assignment_id": int(assignment_id),
                "engineer_id": assignment["engineer_id"],
                "progress_percentage": progress_percentage,
                "notes": notes,
                "updated_at": datetime.now().isoformat(),
                "updated_by": body["user"]["id"]
            }
            app_data["progress"][str(progress_id)] = progress_record
            
            # Update assignment status based on progress
            if progress_percentage == 100:
                assignment["status"] = "completed"
                assignment["completed_at"] = datetime.now().isoformat()
                
                # Unlock the next module in sequence
                engineer_id = assignment["engineer_id"]
                current_sequence = assignment.get("sequence_order", 0)
                next_sequence = current_sequence + 1
                
                # Find and unlock the next module
                for assign_id, assign_data in app_data["assignments"].items():
                    if (assign_data.get("engineer_id") == engineer_id and 
                        assign_data.get("sequence_order") == next_sequence and 
                        assign_data.get("status") == "locked"):
                        assign_data["status"] = "assigned"
                        assign_data["unlocked"] = True
                        assign_data["locked_reason"] = None
                        assign_data["unlocked_at"] = datetime.now().isoformat()
                        
                        # Send notification about unlocked module
                        client.chat_postMessage(
                            channel=body["user"]["id"],
                            text=f"🎉 Great job! Module {current_sequence} completed. Module {next_sequence} is now unlocked and ready to start!"
                        )
                        break
                        
            elif progress_percentage > 0:
                assignment["status"] = "in_progress"
            
            save_data(app_data)
            
            # Send confirmation
            status_emoji = "🎉" if progress_percentage == 100 else "📈" if progress_percentage > 0 else "📝"
            client.chat_postMessage(
                channel=body["user"]["id"],
                text=f"{status_emoji} Progress updated for {module_name}: {progress_percentage}%"
            )
            
            # If completed, send congratulations
            if progress_percentage == 100:
                client.chat_postMessage(
                    channel=body["user"]["id"],
                    text=f"🎉 Congratulations! You've completed {module_name}! Great work!"
                )
            
            # Update home tab
            from ui.home import create_home_view
            client.views_publish(
                user_id=body["user"]["id"],
                view=create_home_view(body["user"]["id"], app_data)
            )
            
        except Exception as e:
            print(f"Error updating progress: {e}")
            client.chat_postMessage(
                channel=body["user"]["id"],
                text="❌ Error updating progress. Please try again."
            )

    @app.view("engineer_report_modal")
    def handle_engineer_report_modal(ack, body, client, view):
        ack()
        
        try:
            from pdf_generator import generate_engineer_report
            import os
            
            app_data = get_app_data()
            values = view["state"]["values"]
            
            # Get selected engineer
            engineer_id = values["engineer_selection"]["selected_engineer"]["selected_option"]["value"]
            
            if engineer_id == "none":
                client.chat_postMessage(
                    channel=body["user"]["id"],
                    text="❌ No engineers available to generate report."
                )
                return
            
            # Get engineer data
            engineer = app_data["engineers"].get(engineer_id)
            if not engineer:
                client.chat_postMessage(
                    channel=body["user"]["id"],
                    text="❌ Engineer not found."
                )
                return
            
            # Get all assignments for this engineer
            engineer_assignments = []
            for assign_id, assign_data in app_data["assignments"].items():
                if assign_data.get("engineer_id") == int(engineer_id):
                    engineer_assignments.append(assign_data)
            
            # Generate PDF
            engineer_name = engineer.get("name", "Unknown").replace(" ", "_")
            filename = f"report_engineer_{engineer_name}_{datetime.now().strftime('%Y%m%d')}.pdf"
            
            generate_engineer_report(engineer, engineer_assignments, app_data, filename)
            
            # Open DM channel with user to get channel ID
            dm_response = client.conversations_open(users=[body["user"]["id"]])
            dm_channel_id = dm_response["channel"]["id"]
            
            # Upload PDF to Slack using files_upload_v2
            with open(filename, 'rb') as f:
                upload_response = client.files_upload_v2(
                    channel=dm_channel_id,
                    file=f,
                    filename=filename,
                    title=f"📊 Engineer Report: {engineer.get('name', 'Unknown')}",
                    initial_comment=f"✅ Generated training report for *{engineer.get('name', 'Unknown')}*\n\n"
                                   f"📊 Stats: {len(engineer_assignments)} total assignments\n"
                                   f"🟢 Completed: {len([a for a in engineer_assignments if a.get('status') == 'completed'])}\n"
                                   f"🟡 In Progress: {len([a for a in engineer_assignments if a.get('status') == 'in_progress'])}"
                )
            
            # Clean up file
            if os.path.exists(filename):
                os.remove(filename)
            
            print(f"✅ Successfully generated and sent engineer PDF report for {engineer.get('name')}")
            
        except Exception as e:
            print(f"Error generating engineer report: {e}")
            import traceback
            traceback.print_exc()
            client.chat_postMessage(
                channel=body["user"]["id"],
                text=f"❌ Error generating report: {str(e)}"
            )

    @app.view("set_end_date_modal")
    def handle_set_end_date_modal(ack, body, client, view):
        ack()
        try:
            from engineer_tenures import set_tenure_end_date
            app_data = get_app_data()
            values = view["state"]["values"]
            tenure_val = values.get("tenure_selection", {}).get("tenure_select", {}).get("selected_option", {}).get("value")
            end_date_str = values.get("end_date_block", {}).get("end_date_picker", {}).get("selected_date")
            if not tenure_val or tenure_val == "none":
                client.chat_postMessage(channel=body["user"]["id"], text="❌ Please select an engineer tenure.")
                return
            if not end_date_str:
                client.chat_postMessage(channel=body["user"]["id"], text="❌ Please select an end date.")
                return
            parts = tenure_val.split("|")
            if len(parts) != 2:
                client.chat_postMessage(channel=body["user"]["id"], text="❌ Invalid selection.")
                return
            eng_id, idx_str = parts[0], parts[1]
            try:
                tenure_index = int(idx_str)
            except ValueError:
                client.chat_postMessage(channel=body["user"]["id"], text="❌ Invalid tenure.")
                return
            engineer = app_data["engineers"].get(eng_id)
            if not engineer:
                client.chat_postMessage(channel=body["user"]["id"], text="❌ Engineer not found.")
                return
            ok, err = set_tenure_end_date(engineer, tenure_index, end_date_str)
            if not ok:
                client.chat_postMessage(channel=body["user"]["id"], text=f"❌ {err}")
                return
            save_data(app_data)
            name = engineer.get("name", "Unknown")
            client.chat_postMessage(
                channel=body["user"]["id"],
                text=f"✅ End date set for *{name}* (tenure index {tenure_index}) to *{end_date_str}*. PDF and Home will show this correctly."
            )
        except Exception as e:
            print(f"Error in set_end_date_modal: {e}")
            client.chat_postMessage(channel=body["user"]["id"], text="❌ Failed to set end date. Please try again.")

    @app.view("talent_profile_modal")
    def handle_talent_profile_modal(ack, body, client, view):
        try:
            from engineer_tenures import get_team, get_geo, get_onboarding_plan, get_all_tenures, get_active_tenures
            app_data = get_app_data()
            values = view["state"]["values"]
            engineer_id = values.get("talent_engineer_selection", {}).get("selected_engineer", {}).get("selected_option", {}).get("value")
            if not engineer_id or engineer_id == "none":
                ack(response_action="errors", errors={"talent_engineer_selection": "Please select an engineer."})
                return
            engineer = app_data["engineers"].get(engineer_id)
            if not engineer:
                ack(response_action="errors", errors={"talent_engineer_selection": "Engineer not found."})
                return
            # Gather assignments
            assignments = [a for a in app_data["assignments"].values() if a.get("engineer_id") == int(engineer_id)]
            completed = [a for a in assignments if a.get("status") == "completed"]
            in_progress = [a for a in assignments if a.get("status") == "in_progress"]
            completion_pct = int((len(completed) / len(assignments) * 100)) if assignments else 0
            name = engineer.get("name", "Unknown")
            email = (engineer.get("email") or "").strip() or "Not on file"
            # Build profile blocks for same-page popup (modal update)
            blocks = [
                {"type": "header", "text": {"type": "plain_text", "text": f"👤 {name}", "emoji": True}},
                {"type": "context", "elements": [{"type": "mrkdwn", "text": f"📧 {email}  ·  Talent Profile"}]},
                {"type": "divider"}
            ]
            # Current role(s)
            active = get_active_tenures(engineer)
            if active:
                role_lines = []
                for t in active:
                    team = t.get("team", "unassigned").replace("_", " ").title()
                    geo = (t.get("geo") or "unassigned").replace("_", " ").title()
                    plan = t.get("onboarding_plan", "custom").replace("_", " ").title()
                    end = (t.get("end_date") or "")[:10] or "Present"
                    role_lines.append(f"• *{team}* · {geo} · {plan} · _{end}_")
                blocks.append({
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": "*📍 Current role(s)*\n" + "\n".join(role_lines)}
                })
            # Experience (team history)
            all_t = get_all_tenures(engineer)
            if all_t:
                exp_lines = []
                for t in all_t:
                    team = t.get("team", "unassigned").replace("_", " ").title()
                    geo = (t.get("geo") or "unassigned").replace("_", " ").title()
                    start = (t.get("start_date") or "")[:10] or "—"
                    end = (t.get("end_date") or "")[:10] if t.get("end_date") else "Present"
                    exp_lines.append(f"• {team} ({geo}) · {start} → {end}")
                blocks.append({
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": "*💼 Experience*\n" + "\n".join(exp_lines)}
                })
            # Learning & readiness
            blocks.append({
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*📊 Completion*\n`{completion_pct}%`"},
                    {"type": "mrkdwn", "text": f"*📚 Assignments*\n`{len(completed)}` completed · `{len(in_progress)}` in progress"},
                ]
            })
            # Skills / modules & assessments completed
            module_names = []
            assessment_names = []
            for a in completed:
                mid = a.get("module_id")
                atype = a.get("type", "module")
                if atype == "module":
                    mod = app_data.get("modules", {}).get(str(mid), {}) if mid is not None else {}
                    name_m = mod.get("name") or (f"Module {mid}" if mid is not None else "Module")
                    if "predefined_" in str(mid or ""):
                        predef = {"0": "Agentforce", "1": "Data Cloud", "2": "Apex", "3": "Integration", "4": "Message Queue", "5": "Deployments"}
                        name_m = predef.get(str(mid).split("_")[-1], name_m)
                    if name_m and name_m not in module_names:
                        module_names.append(name_m)
                else:
                    ass = app_data.get("assessments", {}).get(str(mid), {}) if mid is not None else {}
                    name_a = ass.get("name") or (f"Assessment {mid}" if mid is not None else "Assessment")
                    if name_a and name_a not in assessment_names:
                        assessment_names.append(name_a)
            skills_text = ""
            if module_names:
                skills_text += "*Skills & modules:* " + ", ".join(module_names[:10]) + (" …" if len(module_names) > 10 else "")
            if assessment_names:
                skills_text += "\n*Assessments:* " + ", ".join(assessment_names[:8]) + (" …" if len(assessment_names) > 8 else "")
            if not skills_text:
                skills_text = "_No completed modules or assessments yet._"
            blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": "*🎯 Skills & certifications*\n" + skills_text}})
            blocks.append({"type": "divider"})
            # Export to PDF and Close buttons
            blocks.append({
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Export to PDF", "emoji": True},
                        "action_id": "talent_profile_export_pdf",
                        "style": "primary"
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Close", "emoji": True},
                        "action_id": "talent_profile_close"
                    }
                ]
            })
            # Update modal to show profile in same-page popup (no DM)
            ack(response_action="update", view={
                "type": "modal",
                "callback_id": "talent_profile_display",
                "title": {"type": "plain_text", "text": "Talent Profile"},
                "close": {"type": "plain_text", "text": "Close"},
                "private_metadata": engineer_id,
                "blocks": blocks
            })
        except Exception as e:
            print(f"Error in talent_profile_modal: {e}")
            import traceback
            traceback.print_exc()
            ack()
            client.chat_postMessage(channel=body["user"]["id"], text="❌ Could not load Talent Profile. Please try again.")

    @app.view("module_report_modal")
    def handle_module_report_modal(ack, body, client, view):
        ack()
        
        try:
            from pdf_generator import generate_module_report
            import os
            
            app_data = get_app_data()
            values = view["state"]["values"]
            
            # Predefined modules mapping
            predefined_modules = {
                "0": "Agentforce",
                "1": "Data Cloud",
                "2": "Apex",
                "3": "Integration",
                "4": "Message Queue",
                "5": "Deployments"
            }
            
            # Get selected module
            module_id = values["module_selection"]["selected_module"]["selected_option"]["value"]
            
            if module_id == "none":
                client.chat_postMessage(
                    channel=body["user"]["id"],
                    text="❌ No modules available to generate report."
                )
                return
            
            # Get status filter if provided
            status_filter = None
            if "status_filter" in values and values["status_filter"]["status_select"].get("selected_option"):
                status_filter = values["status_filter"]["status_select"]["selected_option"]["value"]
            
            # Get module name
            if 'predefined_' in module_id:
                actual_id = module_id.split('_')[-1]
                module_name = predefined_modules.get(actual_id, "Unknown Module")
            elif module_id in app_data.get("modules", {}):
                module_name = app_data["modules"][module_id].get("name", "Unknown Module")
            else:
                module_name = f"Module {module_id}"
            
            # Generate PDF
            filename = f"report_module_{module_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.pdf"
            
            generate_module_report(module_id, module_name, app_data, status_filter, filename)
            
            # Open DM channel with user to get channel ID
            dm_response = client.conversations_open(users=[body["user"]["id"]])
            dm_channel_id = dm_response["channel"]["id"]
            
            # Upload PDF to Slack using files_upload_v2
            report_comment = f"✅ Generated module report for *{module_name}*"
            if status_filter and status_filter != "all":
                report_comment += f" (Filter: {status_filter.replace('_', ' ').title()})"
            
            with open(filename, 'rb') as f:
                upload_response = client.files_upload_v2(
                    channel=dm_channel_id,
                    file=f,
                    filename=filename,
                    title=f"📚 Module Report: {module_name}",
                    initial_comment=report_comment
                )
            
            # Clean up file
            if os.path.exists(filename):
                os.remove(filename)
            
            print(f"✅ Successfully generated and sent module PDF report")
            
        except Exception as e:
            print(f"Error generating module report: {e}")
            import traceback
            traceback.print_exc()
            client.chat_postMessage(
                channel=body["user"]["id"],
                text=f"❌ Error generating report: {str(e)}"
            )

    @app.view("assessment_report_modal")
    def handle_assessment_report_modal(ack, body, client, view):
        ack()
        
        try:
            from pdf_generator import generate_assessment_report
            import os
            
            app_data = get_app_data()
            values = view["state"]["values"]
            
            # Get selected assessment
            assessment_id = values["assessment_selection"]["selected_assessment"]["selected_option"]["value"]
            
            if assessment_id == "none":
                client.chat_postMessage(
                    channel=body["user"]["id"],
                    text="❌ No assessments available to generate report."
                )
                return
            
            # Get status filter if provided
            status_filter = None
            if "status_filter" in values and values["status_filter"]["status_select"].get("selected_option"):
                status_filter = values["status_filter"]["status_select"]["selected_option"]["value"]
            
            # Get assessment name
            assessment = app_data.get("assessments", {}).get(assessment_id, {})
            assessment_name = assessment.get("name", "Unknown Assessment")
            
            # Generate PDF
            filename = f"report_assessment_{assessment_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.pdf"
            
            generate_assessment_report(assessment_id, assessment_name, app_data, status_filter, filename)
            
            # Open DM channel with user to get channel ID
            dm_response = client.conversations_open(users=[body["user"]["id"]])
            dm_channel_id = dm_response["channel"]["id"]
            
            # Upload PDF to Slack using files_upload_v2
            report_comment = f"✅ Generated assessment report for *{assessment_name}*"
            if status_filter and status_filter != "all":
                report_comment += f" (Filter: {status_filter.replace('_', ' ').title()})"
            
            with open(filename, 'rb') as f:
                upload_response = client.files_upload_v2(
                    channel=dm_channel_id,
                    file=f,
                    filename=filename,
                    title=f"📋 Assessment Report: {assessment_name}",
                    initial_comment=report_comment
                )
            
            # Clean up file
            if os.path.exists(filename):
                os.remove(filename)
            
            print(f"✅ Successfully generated and sent assessment PDF report")
            
        except Exception as e:
            print(f"Error generating assessment report: {e}")
            import traceback
            traceback.print_exc()
            client.chat_postMessage(
                channel=body["user"]["id"],
                text=f"❌ Error generating report: {str(e)}"
            )

    @app.view("due_report_modal")
    def handle_due_report_modal(ack, body, client, view):
        ack()
        
        try:
            from pdf_generator import generate_due_report
            import os
            
            app_data = get_app_data()
            
            # Generate PDF
            filename = f"report_due_{datetime.now().strftime('%Y%m%d')}.pdf"
            
            generate_due_report(app_data, filename)
            
            # Open DM channel with user to get channel ID
            dm_response = client.conversations_open(users=[body["user"]["id"]])
            dm_channel_id = dm_response["channel"]["id"]
            
            # Upload PDF to Slack using files_upload_v2
            with open(filename, 'rb') as f:
                upload_response = client.files_upload_v2(
                    channel=dm_channel_id,
                    file=f,
                    filename=filename,
                    title="⏰ Due Report - Behind Schedule",
                    initial_comment="✅ Generated due report showing all overdue assignments"
                )
            
            # Clean up file
            if os.path.exists(filename):
                os.remove(filename)
            
            print(f"✅ Successfully generated and sent due report PDF")
            
        except Exception as e:
            print(f"Error generating due report: {e}")
            import traceback
            traceback.print_exc()
            client.chat_postMessage(
                channel=body["user"]["id"],
                text=f"❌ Error generating report: {str(e)}"
            )

    @app.view("detailed_report_modal")
    def handle_detailed_report_modal(ack, body, client, view):
        """DEPRECATED - Legacy handler for old detailed report modal"""
        ack()
        
        try:
            from pdf_generator import generate_engineer_report, generate_module_report, generate_assessment_report, generate_due_report
            import os
            
            app_data = get_app_data()
            values = view["state"]["values"]
            
            # Get report type
            report_type = values["report_type"]["report_type_select"]["selected_option"]["value"]
            
            # Get status filter if provided
            status_filter = None
            if "status_filter" in values and values["status_filter"]["status_select"].get("selected_option"):
                status_filter = values["status_filter"]["status_select"]["selected_option"]["value"]
            
            # Predefined modules mapping
            predefined_modules = {
                "0": "Agentforce",
                "1": "Data Cloud",
                "2": "Apex",
                "3": "Integration",
                "4": "Message Queue",
                "5": "Deployments"
            }
            
            # Generate report based on type
            if report_type == "by_engineer":
                # Get selected engineer
                if "engineer_selection" not in values or not values["engineer_selection"]["selected_engineer"].get("selected_option"):
                    client.chat_postMessage(
                        channel=body["user"]["id"],
                        text="❌ Please select an engineer for 'By Engineer' report."
                    )
                    return
                
                engineer_id = values["engineer_selection"]["selected_engineer"]["selected_option"]["value"]
                
                if engineer_id == "none":
                    client.chat_postMessage(
                        channel=body["user"]["id"],
                        text="❌ No engineers available to generate report."
                    )
                    return
                
                # Get engineer data
                engineer = app_data["engineers"].get(engineer_id)
                if not engineer:
                    client.chat_postMessage(
                        channel=body["user"]["id"],
                        text="❌ Engineer not found."
                    )
                    return
                
                # Get all assignments for this engineer
                engineer_assignments = []
                for assign_id, assign_data in app_data["assignments"].items():
                    if assign_data.get("engineer_id") == int(engineer_id):
                        engineer_assignments.append(assign_data)
                
                # Generate PDF
                engineer_name = engineer.get("name", "Unknown").replace(" ", "_")
                filename = f"report_engineer_{engineer_name}_{datetime.now().strftime('%Y%m%d')}.pdf"
                
                generate_engineer_report(engineer, engineer_assignments, app_data, filename)
                
                report_title = f"📊 Engineer Report: {engineer.get('name', 'Unknown')}"
                report_comment = f"✅ Generated training report for *{engineer.get('name', 'Unknown')}*\n\n" \
                               f"📊 Stats: {len(engineer_assignments)} total assignments\n" \
                               f"🟢 Completed: {len([a for a in engineer_assignments if a.get('status') == 'completed'])}\n" \
                               f"🟡 In Progress: {len([a for a in engineer_assignments if a.get('status') == 'in_progress'])}"
            
            elif report_type == "by_module":
                # Get selected module
                if "module_selection" not in values or not values["module_selection"]["selected_module"].get("selected_option"):
                    client.chat_postMessage(
                        channel=body["user"]["id"],
                        text="❌ Please select a module for 'By Module' report."
                    )
                    return
                
                module_id = values["module_selection"]["selected_module"]["selected_option"]["value"]
                
                if module_id == "none":
                    client.chat_postMessage(
                        channel=body["user"]["id"],
                        text="❌ No modules available to generate report."
                    )
                    return
                
                # Get module name
                if 'predefined_' in module_id:
                    actual_id = module_id.split('_')[-1]
                    module_name = predefined_modules.get(actual_id, "Unknown Module")
                elif module_id in app_data.get("modules", {}):
                    module_name = app_data["modules"][module_id].get("name", "Unknown Module")
                else:
                    module_name = f"Module {module_id}"
                
                # Generate PDF
                filename = f"report_module_{module_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.pdf"
                
                generate_module_report(module_id, module_name, app_data, status_filter, filename)
                
                report_title = f"📚 Module Report: {module_name}"
                report_comment = f"✅ Generated module report for *{module_name}*"
                if status_filter and status_filter != "all":
                    report_comment += f" (Filter: {status_filter.replace('_', ' ').title()})"
            
            elif report_type == "by_assessments":
                # Get selected assessment
                if "assessment_selection" not in values or not values["assessment_selection"]["selected_assessment"].get("selected_option"):
                    client.chat_postMessage(
                        channel=body["user"]["id"],
                        text="❌ Please select an assessment for 'By Assessments' report."
                    )
                    return
                
                assessment_id = values["assessment_selection"]["selected_assessment"]["selected_option"]["value"]
                
                if assessment_id == "none":
                    client.chat_postMessage(
                        channel=body["user"]["id"],
                        text="❌ No assessments available to generate report."
                    )
                    return
                
                # Get assessment name
                assessment = app_data.get("assessments", {}).get(assessment_id, {})
                assessment_name = assessment.get("name", "Unknown Assessment")
                
                # Generate PDF
                filename = f"report_assessment_{assessment_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.pdf"
                
                generate_assessment_report(assessment_id, assessment_name, app_data, status_filter, filename)
                
                report_title = f"📋 Assessment Report: {assessment_name}"
                report_comment = f"✅ Generated assessment report for *{assessment_name}*"
                if status_filter and status_filter != "all":
                    report_comment += f" (Filter: {status_filter.replace('_', ' ').title()})"
            
            elif report_type == "due_report":
                # Generate due report
                filename = f"report_due_{datetime.now().strftime('%Y%m%d')}.pdf"
                
                generate_due_report(app_data, filename)
                
                report_title = "⏰ Due Report - Behind Schedule"
                report_comment = "✅ Generated due report showing all overdue assignments"
            
            else:
                client.chat_postMessage(
                    channel=body["user"]["id"],
                    text="❌ Invalid report type selected."
                )
                return
            
            # Open DM channel with user to get channel ID
            dm_response = client.conversations_open(users=[body["user"]["id"]])
            dm_channel_id = dm_response["channel"]["id"]
            
            # Upload PDF to Slack using files_upload_v2
            with open(filename, 'rb') as f:
                upload_response = client.files_upload_v2(
                    channel=dm_channel_id,
                    file=f,
                    filename=filename,
                    title=report_title,
                    initial_comment=report_comment
                )
            
            # Clean up file
            if os.path.exists(filename):
                os.remove(filename)
            
            print(f"✅ Successfully generated and sent {report_type} PDF report")
            
        except Exception as e:
            print(f"Error generating detailed report: {e}")
            import traceback
            traceback.print_exc()
            client.chat_postMessage(
                channel=body["user"]["id"],
                text=f"❌ Error generating report: {str(e)}"
            )

    @app.view("engineer_selection_modal")
    def handle_engineer_selection_modal(ack, body, client, view):
        ack()
        # This modal just shows selection, no form submission needed
        pass

    @app.view("module_selection_modal")
    def handle_module_selection_modal(ack, body, client, view):
        """Handle module selection for editing"""
        try:
            app_data = get_app_data()
            values = view["state"]["values"]
            
            # Get selected module ID
            module_selection = values.get("module_selection", {}).get("module_select", {})
            selected_option = module_selection.get("selected_option")
            
            if not selected_option:
                ack(response_action="errors", errors={
                    "module_selection": "Please select a module"
                })
                return
            
            module_id = selected_option["value"]
            
            # Get module data
            module = app_data["modules"].get(module_id)
            if not module:
                ack()
                client.chat_postMessage(
                    channel=body["user"]["id"],
                    text="❌ Module not found."
                )
                return
            
            # Add ID to module data for the edit form
            module["id"] = module_id
            
            # Close current modal and open edit modal
            ack(response_action="update", view={
                "type": "modal",
                "callback_id": "module_modal",
                "title": {
                    "type": "plain_text",
                    "text": "✏️ Edit Module"
                },
                "submit": {
                    "type": "plain_text",
                    "text": "Save Module"
                },
                "close": {
                    "type": "plain_text",
                    "text": "Cancel"
                },
                "private_metadata": str(module_id),
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"Edit module: *{module.get('name', 'Unknown')}*"
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
                            "initial_value": module.get("name", "")
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
                            "initial_value": module.get("description", "")
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
                            "initial_value": str(module.get("duration_days", ""))
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
                            "initial_value": module.get("skills", "")
                        },
                        "label": {
                            "type": "plain_text",
                            "text": "Skills Covered"
                        }
                    }
                ]
            })
            
            print(f"✅ Opened edit modal for module {module_id}: {module.get('name')}")
            
        except Exception as e:
            print(f"Error handling module selection: {e}")
            import traceback
            traceback.print_exc()
            ack()
            client.chat_postMessage(
                channel=body["user"]["id"],
                text=f"❌ Error loading module for editing: {str(e)}"
            )

    @app.view("assessment_selection_modal")
    def handle_assessment_selection_modal(ack, body, client, view):
        """Handle assessment selection for editing"""
        try:
            app_data = get_app_data()
            values = view["state"]["values"]
            
            # Get selected assessment ID
            assessment_selection = values.get("assessment_selection", {}).get("assessment_select", {})
            selected_option = assessment_selection.get("selected_option")
            
            if not selected_option:
                ack(response_action="errors", errors={
                    "assessment_selection": "Please select an assessment"
                })
                return
            
            assessment_id = selected_option["value"]
            
            # Get assessment data
            assessment = app_data["assessments"].get(assessment_id)
            if not assessment:
                ack()
                client.chat_postMessage(
                    channel=body["user"]["id"],
                    text="❌ Assessment not found."
                )
                return
            
            # Add ID to assessment data for the edit form
            assessment["id"] = assessment_id
            
            # Migrate old format to new format if needed
            if "questions" in assessment and isinstance(assessment["questions"], int):
                # Old format: questions was just a count
                # Convert to new format: empty list (admin will add questions)
                assessment["questions"] = []
                assessment["migrated"] = True
                save_data(app_data)
                print(f"✅ Migrated assessment {assessment_id} to new question format")
            
            # Open question management modal directly (more intuitive for editing)
            from ui.assessment_editor import create_question_list_modal
            
            questions = assessment.get("questions", [])
            assessment_name = assessment.get("name", "Unknown Assessment")
            
            # Close current modal and open question management
            ack(response_action="update", view=create_question_list_modal(assessment_id, assessment_name, questions))
            
            print(f"✅ Opened question management for assessment {assessment_id}: {assessment_name}")
            
        except Exception as e:
            print(f"Error handling assessment selection: {e}")
            import traceback
            traceback.print_exc()
            ack()
            client.chat_postMessage(
                channel=body["user"]["id"],
                text=f"❌ Error loading assessment for editing: {str(e)}"
            )

    @app.view("locked_module_modal")
    def handle_locked_module_modal(ack, body, client, view):
        ack()
        # This modal just shows information, no form submission needed
        pass

    # Configuration view handlers
    @app.view("module_modal")
    def handle_module_submission(ack, body, client, view):
        ack()
        try:
            app_data = get_app_data()
            values = view["state"]["values"]
            
            # Extract form data
            name = values["module_name"]["name_input"]["value"]
            description = values["module_description"]["description_input"]["value"]
            duration_str = values["module_duration"]["duration_input"]["value"]
            skills = values["module_skills"]["skills_input"]["value"]
            trailhead_url = (values.get("module_trailhead_url", {}).get("trailhead_url_input", {}).get("value") or "").strip()
            
            # Validate duration
            try:
                duration_days = int(duration_str) if duration_str else 0
            except ValueError:
                client.chat_postMessage(
                    channel=body["user"]["id"],
                    text="❌ Invalid duration. Please enter a number."
                )
                return
            
            # Check if editing existing module
            module_id = view.get("private_metadata")
            if module_id:
                # Edit existing module
                if module_id in app_data["modules"]:
                    app_data["modules"][module_id].update({
                        "name": name,
                        "description": description,
                        "duration_days": duration_days,
                        "skills": skills,
                        "trailhead_url": trailhead_url,
                        "updated_at": datetime.now().isoformat()
                    })
                    message = f"✅ Module '{name}' updated successfully!"
                else:
                    client.chat_postMessage(
                        channel=body["user"]["id"],
                        text="❌ Module not found."
                    )
                    return
            else:
                # Create new module
                module_id = app_data["next_ids"]["modules"]
                app_data["next_ids"]["modules"] += 1
                
                app_data["modules"][str(module_id)] = {
                    "id": module_id,
                    "name": name,
                    "description": description,
                    "duration_days": duration_days,
                    "skills": skills,
                    "trailhead_url": trailhead_url,
                    "created_at": datetime.now().isoformat()
                }
                message = f"✅ Module '{name}' created successfully!"
            
            # Save data
            save_data(app_data)
            
            # Send confirmation
            client.chat_postMessage(
                channel=body["user"]["id"],
                text=message
            )
            
        except Exception as e:
            print(f"Error saving module: {e}")
            client.chat_postMessage(
                channel=body["user"]["id"],
                text="❌ Error saving module. Please try again."
            )

    @app.view("assessment_modal")
    def handle_assessment_submission(ack, body, client, view):
        ack()
        try:
            app_data = get_app_data()
            values = view["state"]["values"]
            
            # Extract form data
            name = values["assessment_name"]["name_input"]["value"]
            description = values["assessment_description"]["description_input"]["value"]
            skills = values["assessment_skills"]["skills_input"]["value"]
            duration_str = values["assessment_duration"]["duration_input"]["value"]
            
            # Validate duration
            try:
                duration_minutes = int(duration_str) if duration_str else 0
            except ValueError:
                client.chat_postMessage(
                    channel=body["user"]["id"],
                    text="❌ Invalid duration. Please enter a number."
                )
                return
            
            # Check if editing existing assessment
            assessment_id = view.get("private_metadata")
            if assessment_id:
                # Edit existing assessment
                if assessment_id in app_data["assessments"]:
                    app_data["assessments"][assessment_id].update({
                        "name": name,
                        "description": description,
                        "skills": skills,
                        "duration_minutes": duration_minutes,
                        "updated_at": datetime.now().isoformat()
                    })
                    message = f"✅ Assessment '{name}' updated successfully!"
                else:
                    client.chat_postMessage(
                        channel=body["user"]["id"],
                        text="❌ Assessment not found."
                    )
                    return
            else:
                # Create new assessment
                assessment_id = app_data["next_ids"]["assessments"]
                app_data["next_ids"]["assessments"] += 1
                
                app_data["assessments"][str(assessment_id)] = {
                    "id": assessment_id,
                    "name": name,
                    "description": description,
                    "skills": skills,
                    "duration_minutes": duration_minutes,
                    "created_at": datetime.now().isoformat()
                }
                message = f"✅ Assessment '{name}' created successfully!"
            
            # Save data
            save_data(app_data)
            
            # Send confirmation
            client.chat_postMessage(
                channel=body["user"]["id"],
                text=message
            )
            
        except Exception as e:
            print(f"Error saving assessment: {e}")
            client.chat_postMessage(
                channel=body["user"]["id"],
                text="❌ Error saving assessment. Please try again."
            )

    @app.view("weekly_digest_modal")
    def handle_weekly_digest_submission(ack, body, client, view):
        ack()
        try:
            app_data = get_app_data()
            values = view["state"]["values"]
            
            # Extract settings
            enabled = "enabled" in values.get("digest_enabled", {}).get("enable_digest", {}).get("selected_options", [])
            day = values.get("digest_day", {}).get("day_select", {}).get("selected_option", {}).get("value", "Monday")
            time = values.get("digest_time", {}).get("time_select", {}).get("selected_option", {}).get("value", "09:00")
            include_stats = "stats" in values.get("include_stats", {}).get("include_stats", {}).get("selected_options", [])
            include_assignments = "assignments" in values.get("include_assignments", {}).get("include_assignments", {}).get("selected_options", [])
            
            # Initialize notification settings if not exists
            if "notification_settings" not in app_data:
                app_data["notification_settings"] = {}
            
            app_data["notification_settings"]["weekly_digest"] = {
                "enabled": enabled,
                "day": day,
                "time": time,
                "include_stats": include_stats,
                "include_assignments": include_assignments
            }
            
            # Save data
            save_data(app_data)
            
            # Send confirmation
            client.chat_postMessage(
                channel=body["user"]["id"],
                text=f"✅ Weekly digest settings saved! {'Enabled' if enabled else 'Disabled'} - {day} at {time}"
            )
            
        except Exception as e:
            print(f"Error saving weekly digest settings: {e}")
            client.chat_postMessage(
                channel=body["user"]["id"],
                text="❌ Error saving settings. Please try again."
            )

    @app.view("reminder_settings_modal")
    def handle_reminder_settings_submission(ack, body, client, view):
        ack()
        try:
            app_data = get_app_data()
            values = view["state"]["values"]
            
            # Extract settings
            assignment_due = "enabled" in values.get("assignment_due", {}).get("assignment_due_reminders", {}).get("selected_options", [])
            assignment_overdue = "enabled" in values.get("assignment_overdue", {}).get("overdue_reminders", {}).get("selected_options", [])
            module_unlocked = "enabled" in values.get("module_unlocked", {}).get("module_unlocked_notifications", {}).get("selected_options", [])
            assessment_due = "enabled" in values.get("assessment_due", {}).get("assessment_due_reminders", {}).get("selected_options", [])
            days_before = int(values.get("days_before_due", {}).get("days_before_select", {}).get("selected_option", {}).get("value", "1"))
            overdue_frequency = values.get("overdue_frequency", {}).get("overdue_frequency_select", {}).get("selected_option", {}).get("value", "daily")
            
            # Initialize notification settings if not exists
            if "notification_settings" not in app_data:
                app_data["notification_settings"] = {}
            
            app_data["notification_settings"]["reminders"] = {
                "assignment_due": assignment_due,
                "assignment_overdue": assignment_overdue,
                "module_unlocked": module_unlocked,
                "assessment_due": assessment_due,
                "days_before_due": days_before,
                "overdue_frequency": overdue_frequency
            }
            
            # Save data
            save_data(app_data)
            
            # Send confirmation
            client.chat_postMessage(
                channel=body["user"]["id"],
                text=f"✅ Reminder settings saved! Due reminders: {'Enabled' if assignment_due else 'Disabled'}, Overdue: {'Enabled' if assignment_overdue else 'Disabled'}"
            )
            
        except Exception as e:
            print(f"Error saving reminder settings: {e}")
            client.chat_postMessage(
                channel=body["user"]["id"],
                text="❌ Error saving settings. Please try again."
            )

    @app.view("assessment_submission_modal")
    def handle_assessment_submission(ack, body, client, view):
        ack()
        try:
            app_data = get_app_data()
            values = view["state"]["values"]
            assignment_id = view.get("private_metadata")
            
            # Get assignment details
            assignment = app_data["assignments"].get(assignment_id)
            if not assignment:
                client.chat_postMessage(
                    channel=body["user"]["id"],
                    text="❌ Assignment not found."
                )
                return
            
            # Get assessment details
            assessment_id = assignment.get("module_id")
            assessment = app_data["assessments"].get(str(assessment_id))
            if not assessment:
                client.chat_postMessage(
                    channel=body["user"]["id"],
                    text="❌ Assessment not found."
                )
                return
            
            # Process answers
            user_answers = []
            correct_answers = [1, 1, 2, 1, 1]  # Correct answers for the 5 MCQs
            
            for i in range(1, 6):  # 5 questions
                question_key = f"question_{i}"
                if question_key in values:
                    selected_option = values[question_key][f"question_{i}_answer"]["selected_option"]["value"]
                    # Extract option number from value like "q1_option_1"
                    option_num = int(selected_option.split("_")[-1])
                    user_answers.append(option_num)
                else:
                    user_answers.append(0)  # No answer selected
            
            # Calculate score
            score = sum(1 for user, correct in zip(user_answers, correct_answers) if user == correct)
            total = len(correct_answers)
            
            # Update assignment status
            assignment["status"] = "completed"
            assignment["completed_at"] = datetime.now().isoformat()
            assignment["score"] = score
            assignment["total_questions"] = total
            
            # Check if this is a retake
            is_retake = assignment.get("retake_count", 0) > 0
            if is_retake:
                assignment["final_score"] = score
                assignment["final_percentage"] = (score / total) * 100
            
            # Save progress
            progress_id = app_data["next_ids"]["progress"]
            app_data["next_ids"]["progress"] += 1
            
            app_data["progress"][str(progress_id)] = {
                "id": progress_id,
                "assignment_id": int(assignment_id),
                "engineer_id": assignment["engineer_id"],
                "progress_percentage": 100,
                "score": score,
                "total_questions": total,
                "completed_at": datetime.now().isoformat(),
                "is_retake": is_retake,
                "retake_count": assignment.get("retake_count", 0)
            }
            
            save_data(app_data)
            
            # Show results modal
            from ui.assessment_modal import create_assessment_result_modal
            result_modal = create_assessment_result_modal(
                score, total, correct_answers, user_answers, assessment["name"]
            )
            
            client.views_open(
                trigger_id=body["trigger_id"],
                view=result_modal
            )
            
            # Send confirmation message
            percentage = (score / total) * 100
            passed = percentage >= 70
            status_emoji = "✅" if passed else "❌"
            
            client.chat_postMessage(
                channel=body["user"]["id"],
                text=f"{status_emoji} Assessment completed! Score: {score}/{total} ({percentage:.1f}%) - {'Passed' if passed else 'Failed'}"
            )
            
        except Exception as e:
            print(f"Error processing assessment submission: {e}")
            client.chat_postMessage(
                channel=body["user"]["id"],
                text="❌ Error processing assessment. Please try again."
            )

    @app.view("module_start_modal")
    def handle_module_completion(ack, body, client, view):
        ack()
        try:
            app_data = get_app_data()
            values = view["state"]["values"]
            assignment_id = view.get("private_metadata")
            
            # Check if acknowledge checkbox is checked
            acknowledge_checked = False
            if "acknowledge_checkbox" in values:
                acknowledge_data = values["acknowledge_checkbox"]["acknowledge_completion"]
                if acknowledge_data.get("selected_options"):
                    acknowledge_checked = True
            
            if not acknowledge_checked:
                client.chat_postMessage(
                    channel=body["user"]["id"],
                    text="❌ You must acknowledge that you have completed the module before marking it as complete."
                )
                return
            
            # Temporarily disable materials access requirement for debugging
            # TODO: Re-enable this after fixing the assignment ID tracking
            # user_id = body["user"]["id"]
            # materials_accessed = False
            # 
            # if "materials_accessed" in app_data and user_id in app_data["materials_accessed"]:
            #     accessed_data = app_data["materials_accessed"][user_id]
            #     if str(accessed_data.get("assignment_id")) == str(assignment_id):
            #         materials_accessed = True
            # 
            # if not materials_accessed:
            #     client.chat_postMessage(
            #         channel=body["user"]["id"],
            #         text="❌ You must access the learning materials before completing the module. Please click '🌐 Open Learning Materials' and then '✅ I Have Accessed Learning Materials' first."
            #     )
            #     return
            
            # Get assignment details
            assignment = app_data["assignments"].get(assignment_id)
            if not assignment:
                client.chat_postMessage(
                    channel=body["user"]["id"],
                    text="❌ Assignment not found."
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
                "assignment_id": int(assignment_id),
                "engineer_id": assignment["engineer_id"],
                "progress_percentage": 100,
                "completed_at": datetime.now().isoformat(),
                "type": "module"
            }
            
            save_data(app_data)
            
            # Send confirmation message
            client.chat_postMessage(
                channel=body["user"]["id"],
                text=f"✅ Module '{assignment.get('module_name', 'Unknown Module')}' completed successfully!"
            )
            
        except Exception as e:
            print(f"Error processing module completion: {e}")
            client.chat_postMessage(
                channel=body["user"]["id"],
                text="❌ Error processing module completion. Please try again."
            )
    
    @app.view("search_modal")
    def handle_search_submission(ack, body, client, view):
        """Handle search query submission and display results"""
        ack()
        
        try:
            app_data = get_app_data()
            values = view["state"]["values"]
            
            # Extract search query
            search_query = values["search_input"]["search_query"]["value"]
            
            print(f"🔍 Searching for: {search_query}")
            
            # Perform search
            from ui.search_modal import perform_search, create_search_results_modal
            results = perform_search(search_query, app_data)
            
            print(f"✅ Search found {results['total']} total results")
            print(f"   - Engineers: {len(results['engineers'])}")
            print(f"   - Modules: {len(results['modules'])}")
            print(f"   - Assessments: {len(results['assessments'])}")
            print(f"   - Assignments: {len(results['assignments'])}")
            
            # Open results modal
            client.views_open(
                trigger_id=body["trigger_id"],
                view=create_search_results_modal(search_query, results, app_data)
            )
            
        except Exception as e:
            print(f"Error performing search: {e}")
            import traceback
            traceback.print_exc()
            client.chat_postMessage(
                channel=body["user"]["id"],
                text=f"❌ Error performing search: {str(e)}"
            )