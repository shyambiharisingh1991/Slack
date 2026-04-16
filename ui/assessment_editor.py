def create_assessment_editor_modal(assessment_data=None):
    """Create comprehensive assessment editor with question management
    
    Due to Slack modal limitations, this creates a summary view with buttons
    to manage individual questions.
    """
    is_edit = assessment_data is not None
    assessment_id = assessment_data.get("id") if is_edit else ""
    
    # Handle both old format (questions as int) and new format (questions as list)
    questions_data = assessment_data.get("questions", []) if is_edit else []
    if isinstance(questions_data, int):
        # Old format: questions is a count, convert to empty list
        questions = []
    else:
        questions = questions_data if questions_data else []
    
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"{'✏️ Edit' if is_edit else '➕ Create'} Assessment"
            }
        },
        {
            "type": "input",
            "block_id": "assessment_name",
            "element": {
                "type": "plain_text_input",
                "action_id": "name_input",
                "placeholder": {
                    "type": "plain_text",
                    "text": "Enter assessment name"
                },
                "initial_value": assessment_data.get("name", "") if is_edit else ""
            },
            "label": {
                "type": "plain_text",
                "text": "Assessment Name"
            }
        },
        {
            "type": "input",
            "block_id": "assessment_description",
            "element": {
                "type": "plain_text_input",
                "action_id": "description_input",
                "multiline": True,
                "placeholder": {
                    "type": "plain_text",
                    "text": "Enter assessment description"
                },
                "initial_value": assessment_data.get("description", "") if is_edit else ""
            },
            "label": {
                "type": "plain_text",
                "text": "Description"
            }
        },
        {
            "type": "input",
            "block_id": "assessment_duration",
            "element": {
                "type": "plain_text_input",
                "action_id": "duration_input",
                "placeholder": {
                    "type": "plain_text",
                    "text": "Enter duration in minutes"
                },
                "initial_value": str(assessment_data.get("duration_minutes", "")) if is_edit else ""
            },
            "label": {
                "type": "plain_text",
                "text": "Duration (minutes)"
            }
        },
        {
            "type": "input",
            "block_id": "assessment_skills",
            "element": {
                "type": "plain_text_input",
                "action_id": "skills_input",
                "multiline": True,
                "placeholder": {
                    "type": "plain_text",
                    "text": "Enter skills assessed (one per line)"
                },
                "initial_value": assessment_data.get("skills", "") if is_edit else ""
            },
            "label": {
                "type": "plain_text",
                "text": "Skills Assessed"
            }
        },
        {
            "type": "input",
            "block_id": "assessment_intro_video",
            "element": {
                "type": "plain_text_input",
                "action_id": "intro_video_input",
                "placeholder": {
                    "type": "plain_text",
                    "text": "https://youtube.com/... or any video URL"
                },
                "initial_value": assessment_data.get("intro_video_url", "") if is_edit else ""
            },
            "label": {
                "type": "plain_text",
                "text": "Intro video URL (optional)"
            },
            "optional": True
        },
        {
            "type": "context",
            "elements": [{"type": "mrkdwn", "text": "_Watch this video first, then answer the questions below._"}]
        },
        {
            "type": "divider"
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*📝 Questions ({len(questions)})*\n_After saving basic info, you can add/edit questions_"
            }
        }
    ]
    
    # Show existing questions as a summary
    if questions:
        for i, question in enumerate(questions[:5], 1):  # Show first 5
            q_text = question.get("question", "")[:80]  # Truncate long questions
            if len(question.get("question", "")) > 80:
                q_text += "..."
            
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{i}.* {q_text}\n_{len(question.get('options', []))} options_"
                }
            })
        
        if len(questions) > 5:
            blocks.append({
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"_...and {len(questions) - 5} more questions_"
                    }
                ]
            })
    else:
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "_No questions yet. Save assessment first, then add questions._"
            }
        })
    
    return {
        "type": "modal",
        "callback_id": "assessment_editor_modal",
        "title": {
            "type": "plain_text",
            "text": "Assessment Editor"
        },
        "submit": {
            "type": "plain_text",
            "text": "Save & Continue"
        },
        "close": {
            "type": "plain_text",
            "text": "Cancel"
        },
        "private_metadata": str(assessment_id) if is_edit else "",
        "blocks": blocks
    }


def create_question_list_modal(assessment_id, assessment_name, questions):
    """Create modal showing all questions with edit/delete/reorder buttons"""
    
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"📝 Manage Questions"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Assessment:* {assessment_name}\n*Total Questions:* {len(questions)}"
            }
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "➕ Add New Question"
                    },
                    "style": "primary",
                    "action_id": f"add_question_{assessment_id}"
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "✏️ Edit Assessment Info"
                    },
                    "action_id": f"edit_assessment_info_{assessment_id}"
                }
            ]
        },
        {
            "type": "divider"
        }
    ]
    
    if not questions:
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "_No questions yet. Click 'Add New Question' to create your first question._"
            }
        })
    else:
        for i, question in enumerate(questions):
            q_text = question.get("question", "Unknown question")
            options_count = len(question.get("options", []))
            correct_idx = question.get("correct", 0)
            video_tag = " 📹" if question.get("video_url") else ""

            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Question {i+1}:* {q_text}{video_tag}\n"
                           f"• {options_count} options | Correct answer: Option {correct_idx + 1}"
                },
                "accessory": {
                    "type": "overflow",
                    "options": [
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "✏️ Edit"
                            },
                            "value": f"edit_question_{assessment_id}_{i}"
                        },
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "🗑️ Delete"
                            },
                            "value": f"delete_question_{assessment_id}_{i}"
                        },
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "⬆️ Move Up"
                            },
                            "value": f"move_up_question_{assessment_id}_{i}"
                        },
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "⬇️ Move Down"
                            },
                            "value": f"move_down_question_{assessment_id}_{i}"
                        }
                    ],
                    "action_id": f"question_actions_{i}"
                }
            })
    
    return {
        "type": "modal",
        "callback_id": "question_list_modal",
        "title": {
            "type": "plain_text",
            "text": "Question Management"
        },
        "close": {
            "type": "plain_text",
            "text": "Close"
        },
        "blocks": blocks
    }


def create_question_editor_modal(assessment_id, question_data=None, question_index=None):
    """Create modal for adding or editing a single question"""
    is_edit = question_data is not None
    
    # Get existing data or defaults
    question_text = question_data.get("question", "") if is_edit else ""
    question_video_url = question_data.get("video_url", "") if is_edit else ""
    options = question_data.get("options", ["", "", "", ""]) if is_edit else ["", "", "", ""]
    correct_index = question_data.get("correct", 0) if is_edit else 0
    
    # Ensure we have at least 4 options
    while len(options) < 4:
        options.append("")
    
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"{'✏️ Edit' if is_edit else '➕ Add'} Question"
            }
        },
        {
            "type": "input",
            "block_id": "question_text",
            "element": {
                "type": "plain_text_input",
                "action_id": "question_input",
                "multiline": True,
                "placeholder": {
                    "type": "plain_text",
                    "text": "Enter your question here..."
                },
                "initial_value": question_text
            },
            "label": {
                "type": "plain_text",
                "text": "Question"
            }
        },
        {
            "type": "input",
            "block_id": "question_video_url",
            "element": {
                "type": "plain_text_input",
                "action_id": "video_url_input",
                "placeholder": {
                    "type": "plain_text",
                    "text": "https://... (short video to watch before answering)"
                },
                "initial_value": question_video_url
            },
            "label": {
                "type": "plain_text",
                "text": "Video URL (optional)"
            },
            "optional": True
        },
        {
            "type": "context",
            "elements": [{"type": "mrkdwn", "text": "_Learners will see this video link above the question._"}]
        },
        {
            "type": "divider"
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*Answer Options*\n_Enter 2-4 answer options_"
            }
        },
        {
            "type": "input",
            "block_id": "option_1",
            "element": {
                "type": "plain_text_input",
                "action_id": "option_1_input",
                "placeholder": {
                    "type": "plain_text",
                    "text": "Option 1"
                },
                "initial_value": options[0]
            },
            "label": {
                "type": "plain_text",
                "text": "Option 1"
            }
        },
        {
            "type": "input",
            "block_id": "option_2",
            "element": {
                "type": "plain_text_input",
                "action_id": "option_2_input",
                "placeholder": {
                    "type": "plain_text",
                    "text": "Option 2"
                },
                "initial_value": options[1]
            },
            "label": {
                "type": "plain_text",
                "text": "Option 2"
            }
        },
        {
            "type": "input",
            "block_id": "option_3",
            "element": {
                "type": "plain_text_input",
                "action_id": "option_3_input",
                "placeholder": {
                    "type": "plain_text",
                    "text": "Option 3 (optional)"
                },
                "initial_value": options[2]
            },
            "label": {
                "type": "plain_text",
                "text": "Option 3"
            },
            "optional": True
        },
        {
            "type": "input",
            "block_id": "option_4",
            "element": {
                "type": "plain_text_input",
                "action_id": "option_4_input",
                "placeholder": {
                    "type": "plain_text",
                    "text": "Option 4 (optional)"
                },
                "initial_value": options[3]
            },
            "label": {
                "type": "plain_text",
                "text": "Option 4"
            },
            "optional": True
        },
        {
            "type": "divider"
        },
        {
            "type": "input",
            "block_id": "correct_answer",
            "element": {
                "type": "static_select",
                "placeholder": {
                    "type": "plain_text",
                    "text": "Select correct answer"
                },
                "options": [
                    {
                        "text": {
                            "type": "plain_text",
                            "text": "Option 1"
                        },
                        "value": "0"
                    },
                    {
                        "text": {
                            "type": "plain_text",
                            "text": "Option 2"
                        },
                        "value": "1"
                    },
                    {
                        "text": {
                            "type": "plain_text",
                            "text": "Option 3"
                        },
                        "value": "2"
                    },
                    {
                        "text": {
                            "type": "plain_text",
                            "text": "Option 4"
                        },
                        "value": "3"
                    }
                ],
                "initial_option": {
                    "text": {
                        "type": "plain_text",
                        "text": f"Option {correct_index + 1}"
                    },
                    "value": str(correct_index)
                },
                "action_id": "correct_answer_select"
            },
            "label": {
                "type": "plain_text",
                "text": "Correct Answer"
            }
        }
    ]
    
    # Store metadata to know which question we're editing
    metadata = {
        "assessment_id": assessment_id,
        "question_index": question_index if is_edit else "new"
    }
    import json
    
    return {
        "type": "modal",
        "callback_id": "question_editor_modal",
        "title": {
            "type": "plain_text",
            "text": "Question Editor"
        },
        "submit": {
            "type": "plain_text",
            "text": "Save Question"
        },
        "close": {
            "type": "plain_text",
            "text": "Cancel"
        },
        "private_metadata": json.dumps(metadata),
        "blocks": blocks
    }

