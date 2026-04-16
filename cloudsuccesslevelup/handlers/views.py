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
    
    # Migrate existing assignments on startup
    app_data = get_app_data()
    migrate_existing_assignments(app_data, save_data)
    
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
            
            # Get user info from Slack
            user_info = client.users_info(user=slack_user_id)
            name = user_info["user"]["real_name"] or user_info["user"]["name"]
            email = user_info["user"]["profile"].get("email", "")
            
            # Check if engineer already exists
            existing_engineer = None
            for eng_id, eng_data in app_data["engineers"].items():
                if eng_data.get("slack_user_id") == slack_user_id:
                    existing_engineer = eng_data
                    break
            
            if existing_engineer:
                # Send error message
                client.chat_postMessage(
                    channel=body["user"]["id"],
                    text=f"❌ Engineer {name} is already registered!"
                )
                return
            
            # Create new engineer
            engineer_id = app_data["next_ids"]["engineers"]
            app_data["next_ids"]["engineers"] += 1
            
            new_engineer = {
                "id": engineer_id,
                "name": name,
                "email": email,
                "slack_user_id": slack_user_id,
                "team": team,
                "geo": geo,
                "onboarding_plan": onboarding_plan,
                "role": "engineer",
                "created_at": datetime.now().isoformat()
            }
            
            app_data["engineers"][str(engineer_id)] = new_engineer
            
            # Parse start date and create assignments with proper due dates
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
            
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
            
            # Send confirmation to manager
            client.chat_postMessage(
                channel=body["user"]["id"],
                text=f"✅ Successfully added engineer: {name} to {team_display.get(team, team.title())} team with {plan_display.get(onboarding_plan, onboarding_plan)} onboarding plan. Welcome message sent!"
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
        ack()
        
        try:
            app_data = get_app_data()
            # Extract form data
            values = view["state"]["values"]
            engineer_id = values["engineer_selection"]["engineer_select"]["selected_user"]
            module_value = values["module_selection"]["module_select"]["selected_option"]["value"]
            due_date_str = values["due_date"]["due_date_picker"]["selected_date"]
            
            # Get or create user info (allow any Slack user)
            engineer = None
            for eng_id, eng_data in app_data["engineers"].items():
                if eng_data.get("slack_user_id") == engineer_id:
                    engineer = eng_data
                    engineer["id"] = eng_id
                    break
            
            # If user not found in engineers, create a basic user record
            if not engineer:
                # Get user info from Slack
                try:
                    user_info = client.users_info(user=engineer_id)
                    user_name = user_info["user"]["real_name"] or user_info["user"]["display_name"] or "Unknown User"
                except:
                    user_name = "Unknown User"
                
                # Create basic engineer record
                engineer_id_new = app_data["next_ids"]["engineers"]
                app_data["next_ids"]["engineers"] += 1
                
                engineer = {
                    "id": engineer_id_new,
                    "name": user_name,
                    "email": "",
                    "slack_user_id": engineer_id,
                    "team": "unassigned",
                    "geo": "unassigned", 
                    "onboarding_plan": "custom",
                    "role": "engineer",
                    "created_at": datetime.now().isoformat()
                }
                
                app_data["engineers"][str(engineer_id_new)] = engineer
                engineer["id"] = engineer_id_new
            
            # Validate due date (cannot be in the past)
            from datetime import datetime as dt, date
            try:
                due_date_obj = dt.strptime(due_date_str, "%Y-%m-%d").date()
                today = date.today()
                if due_date_obj < today:
                    client.chat_postMessage(
                        channel=body["user"]["id"],
                        text="❌ Due date cannot be in the past. Please select a future date."
                    )
                    return
            except ValueError:
                client.chat_postMessage(
                    channel=body["user"]["id"],
                    text="❌ Invalid date format. Please try again."
                )
                return
            
            # Handle predefined modules
            predefined_modules = [
                {"name": "Agentforce", "duration": 3, "description": "Learn Salesforce Agentforce platform"},
                {"name": "Data Cloud", "duration": 5, "description": "Master Salesforce Data Cloud capabilities"},
                {"name": "Apex", "duration": 7, "description": "Develop with Salesforce Apex programming"},
                {"name": "Integration", "duration": 4, "description": "Build integrations with Salesforce APIs"},
                {"name": "Message Queue", "duration": 3, "description": "Implement message queuing solutions"},
                {"name": "Deployments", "duration": 2, "description": "Deploy applications using CI/CD"}
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
        ack()
        
        try:
            app_data = get_app_data()
            # Extract form data
            values = view["state"]["values"]
            engineer_id = values["engineer_selection"]["engineer_select"]["selected_user"]
            assessment_value = values["assessment_selection"]["assessment_select"]["selected_option"]["value"]
            due_date_str = values["due_date"]["due_date_picker"]["selected_date"]
            
            # Get or create user info (allow any Slack user)
            engineer = None
            for eng_id, eng_data in app_data["engineers"].items():
                if eng_data.get("slack_user_id") == engineer_id:
                    engineer = eng_data
                    engineer["id"] = eng_id
                    break
            
            # If user not found in engineers, create a basic user record
            if not engineer:
                # Get user info from Slack
                try:
                    user_info = client.users_info(user=engineer_id)
                    user_name = user_info["user"]["real_name"] or user_info["user"]["display_name"] or "Unknown User"
                except:
                    user_name = "Unknown User"
                
                # Create basic engineer record
                engineer_id_new = app_data["next_ids"]["engineers"]
                app_data["next_ids"]["engineers"] += 1
                
                engineer = {
                    "id": engineer_id_new,
                    "name": user_name,
                    "email": "",
                    "slack_user_id": engineer_id,
                    "team": "unassigned",
                    "geo": "unassigned", 
                    "onboarding_plan": "custom",
                    "role": "engineer",
                    "created_at": datetime.now().isoformat()
                }
                
                app_data["engineers"][str(engineer_id_new)] = engineer
                engineer["id"] = engineer_id_new
            
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

    @app.view("detailed_report_modal")
    def handle_detailed_report_modal(ack, body, client, view):
        ack()
        # This modal just shows buttons, no form submission needed
        pass

    @app.view("engineer_selection_modal")
    def handle_engineer_selection_modal(ack, body, client, view):
        ack()
        # This modal just shows selection, no form submission needed
        pass

    @app.view("module_selection_modal")
    def handle_module_selection_modal(ack, body, client, view):
        ack()
        # This modal just shows selection, no form submission needed
        pass

    @app.view("assessment_selection_modal")
    def handle_assessment_selection_modal(ack, body, client, view):
        ack()
        # This modal just shows selection, no form submission needed
        pass

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