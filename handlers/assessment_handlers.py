"""Handlers for assessment question management"""
import json
import re
from datetime import datetime


def register_assessment_handlers(app, get_app_data, save_data):
    """Register all assessment and question management handlers"""
    
    # View submission handlers
    @app.view("assessment_editor_modal")
    def handle_assessment_editor_submission(ack, body, client, view):
        """Handle saving assessment basic info and offer question management"""
        try:
            app_data = get_app_data()
            values = view["state"]["values"]
            
            # Extract form data
            name = values["assessment_name"]["name_input"]["value"]
            description = values["assessment_description"]["description_input"]["value"]
            skills = values["assessment_skills"]["skills_input"]["value"]
            duration_str = values["assessment_duration"]["duration_input"]["value"]
            intro_video_url = (values.get("assessment_intro_video", {}).get("intro_video_input", {}).get("value") or "").strip()
            
            # Validate duration
            try:
                duration_minutes = int(duration_str) if duration_str else 0
            except ValueError:
                ack(response_action="errors", errors={
                    "assessment_duration": "Duration must be a number"
                })
                return
            
            # Check if editing existing assessment or creating new
            assessment_id = view.get("private_metadata")
            
            if assessment_id:
                # Edit existing assessment
                if assessment_id in app_data["assessments"]:
                    app_data["assessments"][assessment_id].update({
                        "name": name,
                        "description": description,
                        "skills": skills,
                        "duration_minutes": duration_minutes,
                        "intro_video_url": intro_video_url or None,
                        "updated_at": datetime.now().isoformat()
                    })
                    message = f"✅ Assessment '{name}' updated successfully!"
                else:
                    ack()
                    client.chat_postMessage(
                        channel=body["user"]["id"],
                        text="❌ Assessment not found."
                    )
                    return
            else:
                # Create new assessment
                assessment_id = str(app_data["next_ids"]["assessments"])
                app_data["next_ids"]["assessments"] += 1
                
                app_data["assessments"][assessment_id] = {
                    "id": int(assessment_id),
                    "name": name,
                    "description": description,
                    "skills": skills,
                    "duration_minutes": duration_minutes,
                    "intro_video_url": intro_video_url or None,
                    "questions": [],  # Initialize empty questions list
                    "created_at": datetime.now().isoformat()
                }
                message = f"✅ Assessment '{name}' created successfully!"
            
            # Save data
            save_data(app_data)
            
            # Get the assessment data
            assessment = app_data["assessments"][assessment_id]
            questions = assessment.get("questions", [])
            
            # If this was called from within the question list modal (views.push), 
            # pop back to it with updated data
            from ui.assessment_editor import create_question_list_modal
            
            # Acknowledge and update to question list modal
            ack(response_action="update", view=create_question_list_modal(
                assessment_id, 
                name,  # Use the updated name
                questions
            ))
            
            # Also send a confirmation message
            client.chat_postMessage(
                channel=body["user"]["id"],
                text=f"✅ {message}"
            )
            
            print(f"✅ Assessment {assessment_id} saved and returned to question list: {name}")
            
        except Exception as e:
            print(f"Error saving assessment: {e}")
            import traceback
            traceback.print_exc()
            ack()
            client.chat_postMessage(
                channel=body["user"]["id"],
                text=f"❌ Error saving assessment: {str(e)}"
            )
    
    @app.view("question_editor_modal")
    def handle_question_editor_submission(ack, body, client, view):
        """Handle saving a question (add or edit)"""
        try:
            app_data = get_app_data()
            values = view["state"]["values"]
            metadata = json.loads(view["private_metadata"])
            
            assessment_id = metadata["assessment_id"]
            question_index = metadata.get("question_index")
            
            # Extract question data
            question_text = values["question_text"]["question_input"]["value"]
            video_url = (values.get("question_video_url", {}).get("video_url_input", {}).get("value") or "").strip()
            
            # Get options (filter out empty ones)
            options = []
            for i in range(1, 5):
                option_value = values.get(f"option_{i}", {}).get(f"option_{i}_input", {}).get("value", "")
                if option_value and option_value.strip():
                    options.append(option_value.strip())
            
            # Validate: need at least 2 options
            if len(options) < 2:
                ack(response_action="errors", errors={
                    "option_2": "At least 2 options are required"
                })
                return
            
            # Get correct answer index
            correct_answer_value = values["correct_answer"]["correct_answer_select"]["selected_option"]["value"]
            correct_index = int(correct_answer_value)
            
            # Validate correct answer is within range
            if correct_index >= len(options):
                ack(response_action="errors", errors={
                    "correct_answer": f"Correct answer must be one of the {len(options)} options provided"
                })
                return
            
            # Create question object
            question_obj = {
                "question": question_text,
                "options": options,
                "correct": correct_index
            }
            question_obj["video_url"] = video_url if video_url else None
            
            # Get assessment
            assessment = app_data["assessments"].get(assessment_id)
            if not assessment:
                ack()
                client.chat_postMessage(
                    channel=body["user"]["id"],
                    text="❌ Assessment not found."
                )
                return
            
            # Initialize questions list if it doesn't exist
            if "questions" not in assessment:
                assessment["questions"] = []
            
            # Add or update question
            if question_index == "new":
                # Add new question
                assessment["questions"].append(question_obj)
                message = "✅ Question added successfully!"
            else:
                # Update existing question
                question_index = int(question_index)
                if 0 <= question_index < len(assessment["questions"]):
                    assessment["questions"][question_index] = question_obj
                    message = "✅ Question updated successfully!"
                else:
                    ack()
                    client.chat_postMessage(
                        channel=body["user"]["id"],
                        text="❌ Question index out of range."
                    )
                    return
            
            # Save data
            assessment["updated_at"] = datetime.now().isoformat()
            save_data(app_data)
            
            # Acknowledge
            ack()
            
            # Send confirmation with option to continue managing questions
            client.chat_postMessage(
                channel=body["user"]["id"],
                text=message,
                blocks=[
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": message + f"\n\n*Total Questions:* {len(assessment['questions'])}"
                        }
                    },
                    {
                        "type": "actions",
                        "elements": [
                            {
                                "type": "button",
                                "text": {
                                    "type": "plain_text",
                                    "text": "📝 Manage Questions"
                                },
                                "style": "primary",
                                "action_id": f"manage_questions_{assessment_id}"
                            }
                        ]
                    }
                ]
            )
            
            print(f"✅ Question saved for assessment {assessment_id}")
            
        except Exception as e:
            print(f"Error saving question: {e}")
            import traceback
            traceback.print_exc()
            ack()
            client.chat_postMessage(
                channel=body["user"]["id"],
                text=f"❌ Error saving question: {str(e)}"
            )
    
    # Action handlers for buttons
    @app.action(re.compile(r"manage_questions_\d+"))
    def handle_manage_questions(ack, body, client):
        """Open question list modal for managing questions"""
        ack()
        try:
            app_data = get_app_data()
            action_id = body["actions"][0]["action_id"]
            assessment_id = action_id.split("_")[-1]
            
            assessment = app_data["assessments"].get(assessment_id)
            if not assessment:
                client.chat_postMessage(
                    channel=body["user"]["id"],
                    text="❌ Assessment not found."
                )
                return
            
            from ui.assessment_editor import create_question_list_modal
            
            questions = assessment.get("questions", [])
            assessment_name = assessment.get("name", "Unknown Assessment")
            
            client.views_open(
                trigger_id=body["trigger_id"],
                view=create_question_list_modal(assessment_id, assessment_name, questions)
            )
            
            print(f"✅ Opened question list for assessment {assessment_id}")
            
        except Exception as e:
            print(f"Error opening question list: {e}")
            import traceback
            traceback.print_exc()
            client.chat_postMessage(
                channel=body["user"]["id"],
                text=f"❌ Error opening question list: {str(e)}"
            )
    
    @app.action(re.compile(r"add_question_\d+"))
    def handle_add_question(ack, body, client):
        """Open question editor for adding a new question"""
        ack()
        try:
            action_id = body["actions"][0]["action_id"]
            assessment_id = action_id.split("_")[-1]
            
            from ui.assessment_editor import create_question_editor_modal
            
            client.views_push(
                trigger_id=body["trigger_id"],
                view=create_question_editor_modal(assessment_id)
            )
            
            print(f"✅ Opened add question modal for assessment {assessment_id}")
            
        except Exception as e:
            print(f"Error opening add question modal: {e}")
            import traceback
            traceback.print_exc()
    
    @app.action(re.compile(r"question_actions_\d+"))
    def handle_question_overflow_actions(ack, body, client):
        """Handle overflow menu actions for questions (edit/delete/move)"""
        ack()
        try:
            app_data = get_app_data()
            
            selected_option = body["actions"][0]["selected_option"]["value"]
            parts = selected_option.split("_")
            action = "_".join(parts[:2])  # edit_question, delete_question, etc.
            assessment_id = parts[2]
            question_index = int(parts[3])
            
            assessment = app_data["assessments"].get(assessment_id)
            if not assessment:
                client.chat_postMessage(
                    channel=body["user"]["id"],
                    text="❌ Assessment not found."
                )
                return
            
            questions = assessment.get("questions", [])
            
            if action == "edit_question":
                # Open question editor with existing question data
                from ui.assessment_editor import create_question_editor_modal
                
                question_data = questions[question_index] if question_index < len(questions) else None
                if question_data:
                    client.views_push(
                        trigger_id=body["trigger_id"],
                        view=create_question_editor_modal(assessment_id, question_data, question_index)
                    )
                    print(f"✅ Opened edit question modal for question {question_index}")
            
            elif action == "delete_question":
                # Delete the question
                if 0 <= question_index < len(questions):
                    deleted_question = questions.pop(question_index)
                    assessment["updated_at"] = datetime.now().isoformat()
                    save_data(app_data)
                    
                    client.chat_postMessage(
                        channel=body["user"]["id"],
                        text=f"✅ Question deleted: '{deleted_question.get('question', 'Unknown')[:50]}...'"
                    )
                    
                    # Refresh the question list modal
                    from ui.assessment_editor import create_question_list_modal
                    client.views_update(
                        view_id=body["view"]["id"],
                        view=create_question_list_modal(assessment_id, assessment.get("name"), questions)
                    )
            
            elif action == "move_up":
                # Move question up
                if question_index > 0:
                    questions[question_index], questions[question_index - 1] = \
                        questions[question_index - 1], questions[question_index]
                    assessment["updated_at"] = datetime.now().isoformat()
                    save_data(app_data)
                    
                    # Refresh the question list modal
                    from ui.assessment_editor import create_question_list_modal
                    client.views_update(
                        view_id=body["view"]["id"],
                        view=create_question_list_modal(assessment_id, assessment.get("name"), questions)
                    )
            
            elif action == "move_down":
                # Move question down
                if question_index < len(questions) - 1:
                    questions[question_index], questions[question_index + 1] = \
                        questions[question_index + 1], questions[question_index]
                    assessment["updated_at"] = datetime.now().isoformat()
                    save_data(app_data)
                    
                    # Refresh the question list modal
                    from ui.assessment_editor import create_question_list_modal
                    client.views_update(
                        view_id=body["view"]["id"],
                        view=create_question_list_modal(assessment_id, assessment.get("name"), questions)
                    )
            
        except Exception as e:
            print(f"Error handling question action: {e}")
            import traceback
            traceback.print_exc()
            client.chat_postMessage(
                channel=body["user"]["id"],
                text=f"❌ Error: {str(e)}"
            )
    
    @app.action(re.compile(r"edit_assessment_info_\d+"))
    def handle_edit_assessment_info(ack, body, client):
        """Open assessment basic info editor"""
        ack()
        try:
            app_data = get_app_data()
            action_id = body["actions"][0]["action_id"]
            assessment_id = action_id.split("_")[-1]
            
            assessment = app_data["assessments"].get(assessment_id)
            if not assessment:
                client.chat_postMessage(
                    channel=body["user"]["id"],
                    text="❌ Assessment not found."
                )
                return
            
            # Add ID for the edit form
            assessment["id"] = assessment_id
            
            from ui.assessment_editor import create_assessment_editor_modal
            
            # Push the basic info editor modal on top
            client.views_push(
                trigger_id=body["trigger_id"],
                view=create_assessment_editor_modal(assessment)
            )
            
            print(f"✅ Opened basic info editor for assessment {assessment_id}")
            
        except Exception as e:
            print(f"Error opening assessment info editor: {e}")
            import traceback
            traceback.print_exc()
            client.chat_postMessage(
                channel=body["user"]["id"],
                text=f"❌ Error opening editor: {str(e)}"
            )
    
    @app.action(re.compile(r"back_to_assessment_\d+"))
    def handle_back_to_assessment(ack, body, client):
        """Handle back to assessment button"""
        ack()
        # Just close the modal - user can reopen from configurations
        print("User clicked back to assessment")

