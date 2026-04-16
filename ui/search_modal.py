"""Search functionality for the Learning Management System"""
from engineer_tenures import get_team, get_geo, get_onboarding_plan

def create_search_modal():
    """Create the initial search modal with input field"""
    return {
        "type": "modal",
        "callback_id": "search_modal",
        "title": {
            "type": "plain_text",
            "text": "🔍 Search"
        },
        "submit": {
            "type": "plain_text",
            "text": "Search"
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
                    "text": "🔍 Search Everything"
                }
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": "Search across engineers, modules, assessments, and assignments"
                    }
                ]
            },
            {
                "type": "input",
                "block_id": "search_input",
                "element": {
                    "type": "plain_text_input",
                    "action_id": "search_query",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "Enter name, keyword, or ID..."
                    },
                    "min_length": 1
                },
                "label": {
                    "type": "plain_text",
                    "text": "Search Query"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*💡 Search Tips:*\n• Search by engineer name, email, or team\n• Search module or assessment names\n• Search assignment status or IDs\n• Case-insensitive matching"
                }
            }
        ]
    }


def create_search_results_modal(search_query, results, app_data):
    """Create modal displaying search results
    
    Args:
        search_query: The search term entered
        results: Dictionary with categorized results
        app_data: Full app data for additional lookups
    """
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"🔍 Results for \"{search_query}\""
            }
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"Found {results['total']} results across all categories"
                }
            ]
        },
        {
            "type": "divider"
        }
    ]
    
    # Engineers section
    if results['engineers']:
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*👥 Engineers* (`{len(results['engineers'])}` found)"
            }
        })
        
        for engineer in results['engineers'][:5]:  # Limit to 5
            engineer_id = engineer['id']
            
            # Get assignment stats
            eng_assignments = [a for a in app_data["assignments"].values() 
                             if a.get("engineer_id") == int(engineer_id)]
            total = len(eng_assignments)
            completed = len([a for a in eng_assignments if a.get("status") == "completed"])
            
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{engineer['name']}*\n"
                           f"📧 {engineer.get('email', 'N/A')} | "
                           f"🏢 {engineer.get('team', 'unassigned').replace('_', ' ').title()}\n"
                           f"📊 Progress: {completed}/{total} completed"
                }
            })
        
        if len(results['engineers']) > 5:
            blocks.append({
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"_+{len(results['engineers']) - 5} more engineers..._"
                    }
                ]
            })
        
        blocks.append({"type": "divider"})
    
    # Modules section
    if results['modules']:
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*📚 Modules* (`{len(results['modules'])}` found)"
            }
        })
        
        for module in results['modules'][:5]:  # Limit to 5
            # Count assignments for this module
            module_assignments = [a for a in app_data["assignments"].values() 
                                if str(a.get("module_id")) == module['id'] or 
                                a.get("module_id") == f"predefined_{module['id']}"]
            assigned_count = len(module_assignments)
            
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{module['name']}*\n"
                           f"📝 {module.get('description', 'No description')}\n"
                           f"👥 Assigned to {assigned_count} engineer(s)"
                }
            })
        
        if len(results['modules']) > 5:
            blocks.append({
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"_+{len(results['modules']) - 5} more modules..._"
                    }
                ]
            })
        
        blocks.append({"type": "divider"})
    
    # Assessments section
    if results['assessments']:
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*📋 Assessments* (`{len(results['assessments'])}` found)"
            }
        })
        
        for assessment in results['assessments'][:5]:  # Limit to 5
            # Count assignments for this assessment
            assessment_assignments = [a for a in app_data["assignments"].values() 
                                     if str(a.get("module_id")) == assessment['id'] and 
                                     a.get("type") == "assessment"]
            assigned_count = len(assessment_assignments)
            
            qs = assessment.get('questions', [])
            num_questions = len(qs) if isinstance(qs, list) else (qs if isinstance(qs, int) else 0)
            duration = assessment.get('duration_minutes', 0)
            
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{assessment['name']}*\n"
                           f"📝 {assessment.get('description', 'No description')}\n"
                           f"❓ {num_questions} questions | ⏱️ {duration} min | "
                           f"👥 Assigned to {assigned_count} engineer(s)"
                }
            })
        
        if len(results['assessments']) > 5:
            blocks.append({
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"_+{len(results['assessments']) - 5} more assessments..._"
                    }
                ]
            })
        
        blocks.append({"type": "divider"})
    
    # Assignments section
    if results['assignments']:
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*📝 Assignments* (`{len(results['assignments'])}` found)"
            }
        })
        
        for assignment in results['assignments'][:5]:  # Limit to 5
            # Get engineer name
            engineer_id = str(assignment.get('engineer_id'))
            engineer_name = "Unknown"
            if engineer_id in app_data["engineers"]:
                engineer_name = app_data["engineers"][engineer_id].get("name", "Unknown")
            
            # Get module/assessment name
            module_id = assignment.get('module_id')
            item_name = "Unknown"
            item_type = assignment.get('type', 'module')
            
            if item_type == "assessment" and str(module_id) in app_data["assessments"]:
                item_name = app_data["assessments"][str(module_id)].get("name", "Unknown")
            elif str(module_id) in app_data["modules"]:
                item_name = app_data["modules"][str(module_id)].get("name", "Unknown")
            elif isinstance(module_id, str) and module_id.startswith("predefined_"):
                predefined_modules = ["Agentforce", "Data Cloud", "Apex", "Integration", "Message Queue", "Deployments"]
                idx = int(module_id.split("_")[1])
                if 0 <= idx < len(predefined_modules):
                    item_name = predefined_modules[idx]
            
            # Status emoji
            status_emoji = {
                "completed": "✅",
                "in_progress": "🔄",
                "assigned": "📝",
                "locked": "🔒"
            }.get(assignment.get('status', 'assigned'), "📝")
            
            due_date = assignment.get('due_date', 'No due date')
            
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"{status_emoji} *{item_name}*\n"
                           f"👤 {engineer_name} | 📅 Due: {due_date}\n"
                           f"Status: {assignment.get('status', 'assigned').replace('_', ' ').title()}"
                }
            })
        
        if len(results['assignments']) > 5:
            blocks.append({
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"_+{len(results['assignments']) - 5} more assignments..._"
                    }
                ]
            })
    
    # No results message
    if results['total'] == 0:
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"🔍 No Results for \"{search_query}\""
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "😞 *No matches found*\n\n"
                           "*Try:*\n"
                           "• Using different keywords\n"
                           "• Checking spelling\n"
                           "• Using partial names\n"
                           "• Searching by status (completed, assigned, etc.)"
                }
            }
        ]
    
    # Add footer
    blocks.append({
        "type": "context",
        "elements": [
            {
                "type": "mrkdwn",
                "text": "💡 *Tip:* Results are limited to 5 per category. Refine your search for more specific results."
            }
        ]
    })
    
    return {
        "type": "modal",
        "callback_id": "search_results_modal",
        "title": {
            "type": "plain_text",
            "text": "Search Results"
        },
        "close": {
            "type": "plain_text",
            "text": "Close"
        },
        "blocks": blocks
    }


def perform_search(search_query, app_data):
    """Perform comprehensive search across all app data
    
    Args:
        search_query: The search term
        app_data: Complete application data
        
    Returns:
        Dictionary with categorized results
    """
    query_lower = search_query.lower().strip()
    
    results = {
        'engineers': [],
        'modules': [],
        'assessments': [],
        'assignments': [],
        'total': 0
    }
    
    # Search engineers
    for eng_id, engineer in app_data["engineers"].items():
        # Search in name, email, team, geo, role
        searchable_text = " ".join([
            engineer.get('name', '').lower(),
            engineer.get('email', '').lower(),
            get_team(engineer).lower(),
            get_geo(engineer).lower(),
            engineer.get('role', '').lower(),
            get_onboarding_plan(engineer).lower(),
            str(eng_id)
        ])
        if query_lower in searchable_text:
            results['engineers'].append({
                'id': eng_id,
                'name': engineer.get('name', 'Unknown'),
                'email': engineer.get('email', ''),
                'team': get_team(engineer)
            })
    
    # Search modules (including predefined ones)
    predefined_modules = [
        {"id": "0", "name": "Agentforce", "description": "Learn Salesforce Agentforce platform"},
        {"id": "1", "name": "Data Cloud", "description": "Master Salesforce Data Cloud capabilities"},
        {"id": "2", "name": "Apex", "description": "Develop with Salesforce Apex programming"},
        {"id": "3", "name": "Integration", "description": "Build integrations with Salesforce APIs"},
        {"id": "4", "name": "Message Queue", "description": "Implement message queuing solutions"},
        {"id": "5", "name": "Deployments", "description": "Deploy applications using CI/CD"}
    ]
    
    # Search predefined modules
    for module in predefined_modules:
        searchable_text = " ".join([
            module['name'].lower(),
            module.get('description', '').lower(),
            module['id']
        ])
        
        if query_lower in searchable_text:
            results['modules'].append(module)
    
    # Search custom modules
    for mod_id, module in app_data["modules"].items():
        searchable_text = " ".join([
            module.get('name', '').lower(),
            module.get('description', '').lower(),
            module.get('category', '').lower(),
            module.get('skills', '').lower(),
            str(mod_id)
        ])
        
        if query_lower in searchable_text:
            results['modules'].append({
                'id': mod_id,
                'name': module.get('name', 'Unknown'),
                'description': module.get('description', '')
            })
    
    # Search assessments
    for assess_id, assessment in app_data["assessments"].items():
        searchable_text = " ".join([
            assessment.get('name', '').lower(),
            assessment.get('description', '').lower(),
            assessment.get('skills', '').lower(),
            str(assess_id)
        ])
        
        if query_lower in searchable_text:
            qs = assessment.get('questions', [])
            qs = qs if isinstance(qs, list) else []
            results['assessments'].append({
                'id': assess_id,
                'name': assessment.get('name', 'Unknown'),
                'description': assessment.get('description', ''),
                'questions': qs,
                'duration_minutes': assessment.get('duration_minutes', 0)
            })
    
    # Search assignments
    for assign_id, assignment in app_data["assignments"].items():
        # Get engineer name for searching
        engineer_id = str(assignment.get('engineer_id'))
        engineer_name = ""
        if engineer_id in app_data["engineers"]:
            engineer_name = app_data["engineers"][engineer_id].get("name", "").lower()
        
        # Get module/assessment name for searching
        module_id = assignment.get('module_id')
        item_name = ""
        
        if assignment.get('type') == "assessment" and str(module_id) in app_data["assessments"]:
            item_name = app_data["assessments"][str(module_id)].get("name", "").lower()
        elif str(module_id) in app_data["modules"]:
            item_name = app_data["modules"][str(module_id)].get("name", "").lower()
        
        searchable_text = " ".join([
            engineer_name,
            item_name,
            assignment.get('status', '').lower(),
            assignment.get('type', '').lower(),
            str(assign_id)
        ])
        
        if query_lower in searchable_text:
            results['assignments'].append({
                'id': assign_id,
                'engineer_id': assignment.get('engineer_id'),
                'module_id': module_id,
                'status': assignment.get('status'),
                'type': assignment.get('type', 'module'),
                'due_date': assignment.get('due_date', '')
            })
    
    # Calculate total
    results['total'] = (len(results['engineers']) + len(results['modules']) + 
                       len(results['assessments']) + len(results['assignments']))
    
    return results

