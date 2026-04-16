def create_assessment_modal(assessment_data, assignment_id):
    """Create modal for taking an assessment with MCQs"""
    
    # Sample MCQs for the assessment
    mcqs = [
        {
            "question": "What is the primary purpose of HTML?",
            "options": [
                "Styling web pages",
                "Creating the structure of web pages", 
                "Adding interactivity to web pages",
                "Managing databases"
            ],
            "correct": 1
        },
        {
            "question": "Which CSS property is used to change the text color?",
            "options": [
                "text-color",
                "color",
                "font-color", 
                "text-style"
            ],
            "correct": 1
        },
        {
            "question": "What does JavaScript primarily add to web pages?",
            "options": [
                "Visual styling",
                "Database connectivity",
                "Interactivity and dynamic behavior",
                "Server-side processing"
            ],
            "correct": 2
        },
        {
            "question": "Which HTML tag is used to create a hyperlink?",
            "options": [
                "<link>",
                "<a>",
                "<href>",
                "<url>"
            ],
            "correct": 1
        },
        {
            "question": "What is the purpose of CSS frameworks like Bootstrap?",
            "options": [
                "To replace HTML",
                "To provide pre-built styling components",
                "To create databases",
                "To write JavaScript"
            ],
            "correct": 1
        }
    ]
    
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"📋 {assessment_data.get('name', 'Assessment')}"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Description:* {assessment_data.get('description', 'Test your knowledge')}\n*Duration:* {assessment_data.get('duration_minutes', 30)} minutes\n*Questions:* {len(mcqs)}"
            }
        },
        {
            "type": "divider"
        }
    ]
    
    # Add each MCQ as a section
    for i, mcq in enumerate(mcqs, 1):
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Question {i}:* {mcq['question']}"
            }
        })
        
        # Add options as radio buttons
        options = []
        for j, option in enumerate(mcq['options']):
            options.append({
                "text": {
                    "type": "plain_text",
                    "text": option
                },
                "value": f"q{i}_option_{j}"
            })
        
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "Select your answer:"
            },
            "accessory": {
                "type": "radio_buttons",
                "options": options,
                "action_id": f"question_{i}_answer"
            },
            "block_id": f"question_{i}"
        })
        
        blocks.append({
            "type": "divider"
        })
    
    return {
        "type": "modal",
        "callback_id": "assessment_submission_modal",
        "title": {
            "type": "plain_text",
            "text": "Take Assessment"
        },
        "submit": {
            "type": "plain_text",
            "text": "Submit Assessment"
        },
        "close": {
            "type": "plain_text",
            "text": "Cancel"
        },
        "private_metadata": str(assignment_id),
        "blocks": blocks
    }

def create_assessment_result_modal(score, total, correct_answers, user_answers, assessment_name):
    """Create modal showing assessment results"""
    
    percentage = (score / total) * 100
    passed = percentage >= 70  # Assuming 70% is passing
    
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"📊 Assessment Results - {assessment_name}"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Score:* {score}/{total} ({percentage:.1f}%)\n*Status:* {'✅ Passed' if passed else '❌ Failed'}\n*Passing Score:* 70%"
            }
        },
        {
            "type": "divider"
        }
    ]
    
    # Add detailed results for each question
    for i, (correct, user) in enumerate(zip(correct_answers, user_answers), 1):
        is_correct = correct == user
        status_emoji = "✅" if is_correct else "❌"
        
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"{status_emoji} *Question {i}*\nYour answer: {user}\nCorrect answer: {correct}"
            }
        })
        
        if i < len(correct_answers):
            blocks.append({
                "type": "divider"
            })
    
    return {
        "type": "modal",
        "callback_id": "assessment_result_modal",
        "title": {
            "type": "plain_text",
            "text": "Assessment Results"
        },
        "close": {
            "type": "plain_text",
            "text": "Close"
        },
        "blocks": blocks
    }

def create_assessment_completion_modal(assignment, assessment, progress_data):
    """Create modal showing assessment completion status with retake option"""
    
    score = progress_data.get("score", 0)
    total = progress_data.get("total_questions", 5)
    percentage = (score / total) * 100
    completed_at = progress_data.get("completed_at", "Unknown")
    
    # Check if user can retake (score < 80%)
    can_retake = percentage < 80
    
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"📋 Assessment Status - {assessment['name']}"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Status:* ✅ Completed\n*Score:* {score}/{total} ({percentage:.1f}%)\n*Completed:* {completed_at}\n*Due Date:* {assignment.get('due_date', 'No due date')}"
            }
        }
    ]
    
    if can_retake:
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Retake Available:* Your score ({percentage:.1f}%) is below 80%. You can retake this assessment to improve your score."
            }
        })
        blocks.append({
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "🔄 Retake Assessment"
                    },
                    "action_id": f"retake_assessment_{assignment['id']}",
                    "style": "primary"
                }
            ]
        })
    else:
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Excellent Work!* 🎉 You scored {percentage:.1f}% which meets the 80% requirement. No retake needed!"
            }
        })
    
    return {
        "type": "modal",
        "callback_id": "assessment_completion_modal",
        "title": {
            "type": "plain_text",
            "text": "Assessment Status"
        },
        "close": {
            "type": "plain_text",
            "text": "Close"
        },
        "blocks": blocks
    }
