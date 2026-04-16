import json
from datetime import datetime, timedelta
from auth import is_admin, get_user_role
from engineer_tenures import get_team, get_current_tenure, get_active_tenures
from trailhead import fetch_trailhead_profile


def _time_greeting():
    """Return a time-aware greeting word."""
    hour = datetime.now().hour
    if hour < 12:
        return "Good morning"
    elif hour < 17:
        return "Good afternoon"
    return "Good evening"


def _build_alerts(user_is_admin, app_data, engineer):
    """Build attention alert lines for the greeting section."""
    alerts = []
    if user_is_admin:
        # Pending unlock requests
        pending = sum(1 for p in app_data["progress"].values()
                      if p.get("unlock_requested") and not p.get("unlock_approved"))
        if pending:
            alerts.append(f":bell: *{pending}* pending unlock request{'s' if pending != 1 else ''}")

        # Engineers with zero completed assignments
        zero_progress = []
        for eng_id, eng_data in app_data["engineers"].items():
            eng_assigns = [a for a in app_data["assignments"].values()
                           if a.get("engineer_id") == int(eng_id)]
            if eng_assigns and all(a.get("status") != "completed" for a in eng_assigns):
                zero_progress.append(eng_data.get("name", "Unknown"))
        if zero_progress:
            names = ", ".join(zero_progress[:3])
            extra = f" +{len(zero_progress) - 3} more" if len(zero_progress) > 3 else ""
            alerts.append(f":warning: *{len(zero_progress)}* engineer{'s' if len(zero_progress) != 1 else ''} with 0% progress ({names}{extra})")

        # Overdue assignments (due_date in the past, not completed)
        today = datetime.now().strftime("%Y-%m-%d")
        overdue = sum(1 for a in app_data["assignments"].values()
                      if a.get("due_date") and a["due_date"] < today and a.get("status") != "completed")
        if overdue:
            alerts.append(f":rotating_light: *{overdue}* overdue assignment{'s' if overdue != 1 else ''}")

    if engineer:
        eng_assigns = [a for a in app_data["assignments"].values()
                       if a.get("engineer_id") == int(engineer["id"])]
        in_progress = [a for a in eng_assigns if a.get("status") == "in_progress"]
        if in_progress:
            mod_id = in_progress[0].get("module_id")
            mod_name = app_data["modules"].get(str(mod_id), {}).get("name", "your current module")
            alerts.append(f":dart: Continue *{mod_name}*")
        elif eng_assigns and all(a.get("status") != "completed" for a in eng_assigns):
            alerts.append(f":rocket: You have *{len(eng_assigns)}* modules waiting — time to get started!")

    return alerts


def _completion_label(rate, total):
    """Return a contextual label for the completion rate."""
    if total == 0:
        return ":inbox_tray: No assignments yet"
    if rate == 0:
        return f":warning: `{rate}%` — No completions yet"
    if rate < 25:
        return f":small_red_triangle: `{rate}%` — Just getting started"
    if rate < 50:
        return f":large_orange_diamond: `{rate}%` — Making progress"
    if rate < 75:
        return f":large_blue_diamond: `{rate}%` — Over halfway!"
    if rate < 100:
        return f":star2: `{rate}%` — Almost there!"
    return f":tada: `{rate}%` — All complete!"

def _get_assign_key(app_data, assign):
    """Return the dict key for an assignment (needed for action IDs)."""
    assign_id = assign.get("id")
    if assign_id is not None:
        # Try direct key lookup first
        key = str(assign_id)
        if key in app_data["assignments"]:
            return key
        # Fall back to scanning for matching id field
        for k, v in app_data["assignments"].items():
            if v.get("id") == assign_id:
                return k
    return str(assign_id or "0")


def _effective_status(assign):
    """Determine the effective display status of an assignment.

    An assignment is truly locked only if status is 'locked' AND unlocked is
    not True.  This handles legacy assignments and the unlock-on-complete flow.
    """
    status = assign.get("status", "assigned")
    if status == "locked" and assign.get("unlocked"):
        return "assigned"  # unlocked but not yet started
    return status


def _build_path_summary(engineer_assignments, app_data):
    """Build a compact learning path: status counts + the active/upcoming modules.

    Returns (summary_text, active_buttons, completed_text).
    """
    sorted_assigns = sorted(
        engineer_assignments,
        key=lambda a: (a.get("sequence_order") or 0, a.get("id", 0))
    )

    completed = [a for a in sorted_assigns if _effective_status(a) == "completed"]
    in_progress = [a for a in sorted_assigns if _effective_status(a) == "in_progress"]
    ready = [a for a in sorted_assigns if _effective_status(a) == "assigned"]
    locked = [a for a in sorted_assigns if _effective_status(a) == "locked"]

    # One-line status bar
    parts = []
    if completed:
        parts.append(f":white_check_mark: {len(completed)} completed")
    if in_progress:
        parts.append(f":arrow_forward: {len(in_progress)} in progress")
    if ready:
        parts.append(f":radio_button: {len(ready)} ready")
    if locked:
        parts.append(f":lock: {len(locked)} locked")
    summary = "  ·  ".join(parts) if parts else "No assignments"

    # Build clickable buttons for current + next upcoming (up to 3)
    active_assigns = in_progress + ready + locked  # priority order
    buttons = []
    for assign in active_assigns[:3]:
        mod_id = assign.get("module_id")
        mod_name = app_data["modules"].get(str(mod_id), {}).get("name", "Module") if mod_id else "Module"
        if len(mod_name) > 25:
            mod_name = mod_name[:22] + "..."
        eff_status = _effective_status(assign)
        assign_key = _get_assign_key(app_data, assign)

        if eff_status == "in_progress":
            btn = {
                "type": "button",
                "text": {"type": "plain_text", "text": f":arrow_forward: {mod_name}", "emoji": True},
                "style": "primary",
                "action_id": f"start_module_{assign_key}"
            }
        elif eff_status == "locked":
            btn = {
                "type": "button",
                "text": {"type": "plain_text", "text": f":lock: {mod_name}", "emoji": True},
                "action_id": f"start_module_{assign_key}"
            }
        else:
            # assigned / ready — unlocked, can be started
            btn = {
                "type": "button",
                "text": {"type": "plain_text", "text": f":arrow_forward: {mod_name}", "emoji": True},
                "action_id": f"start_module_{assign_key}"
            }
        buttons.append(btn)

    # Completed modules as compact list (show last 3)
    completed_text = ""
    if completed:
        recent_done = completed[-3:]
        names = []
        for a in recent_done:
            mid = a.get("module_id")
            name = app_data["modules"].get(str(mid), {}).get("name", "Module") if mid else "Module"
            names.append(name)
        completed_text = ":white_check_mark: " + "  ·  ".join(f"~{n}~" for n in names)
        if len(completed) > 3:
            completed_text += f"  _+{len(completed) - 3} more_"

    return summary, buttons, completed_text


def _build_recent_activity(app_data, limit=5):
    """Build a recent activity / wins feed from completed assignments."""
    events = []

    # Completed assignments
    for assign_id, assign in app_data["assignments"].items():
        if assign.get("status") == "completed" and assign.get("completed_at"):
            eng_id = assign.get("engineer_id")
            eng_name = app_data["engineers"].get(str(eng_id), {}).get("name", "Unknown")
            mod_id = assign.get("module_id")
            mod_name = app_data["modules"].get(str(mod_id), {}).get("name", "a module") if mod_id else "a module"
            events.append({
                "timestamp": assign["completed_at"],
                "text": f":tada: *{eng_name}* completed _{mod_name}_"
            })

    # Sort newest first
    events.sort(key=lambda e: e["timestamp"], reverse=True)
    return events[:limit]


def create_home_view(user_id, app_data, selected_engineer_id=None):
    """Create a beautiful, professional home tab view with enhanced visuals
    
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
    total_assignments = len(app_data["assignments"])
    completed_assignments = len([a for a in app_data["assignments"].values() if a.get("status") == "completed"])
    pending_requests = sum(1 for progress in app_data["progress"].values() 
                          if progress.get("unlock_requested") and not progress.get("unlock_approved"))
    
    # Calculate completion rate
    completion_rate = int((completed_assignments / total_assignments * 100)) if total_assignments > 0 else 0
    
    # Role-based welcome message
    role_display = "Administrator" if user_role == "admin" else "Manager" if user_role == "manager" else "Engineer"
    
    # --- Personalized greeting ---
    display_name = engineer.get("name", "").split()[0] if engineer else None
    greeting = _time_greeting()
    greeting_text = f"{greeting}, {display_name} :wave:" if display_name else f"{greeting} :wave:"

    alerts = _build_alerts(user_is_admin, app_data, engineer)

    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": greeting_text,
                "emoji": True
            }
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f":mortar_board: *CloudSuccess LevelUp*  |  {role_display}  |  {datetime.now().strftime('%a, %b %d')}"
                }
            ]
        }
    ]

    # Attention alerts
    if alerts:
        alert_text = "\n".join(alerts)
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Needs your attention:*\n{alert_text}"
            },
            "accessory": {
                "type": "button",
                "text": {"type": "plain_text", "text": ":mag: Search", "emoji": True},
                "action_id": "open_search_modal"
            }
        })
    else:
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": ":white_check_mark: *All clear* — nothing needs your attention right now."
            },
            "accessory": {
                "type": "button",
                "text": {"type": "plain_text", "text": ":mag: Search", "emoji": True},
                "action_id": "open_search_modal"
            }
        })

    blocks.append({"type": "divider"})
    
    # Admin action buttons - grouped by frequency
    if user_is_admin:
        blocks.extend([
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*:zap: Manage*"
                }
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": ":heavy_plus_sign: Add Engineer", "emoji": True},
                        "style": "primary",
                        "action_id": "add_engineer_button"
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": ":books: Assign Module", "emoji": True},
                        "action_id": "assign_module_button"
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": ":bar_chart: Reports", "emoji": True},
                        "action_id": "detailed_report_button"
                    }
                ]
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": ":clipboard: Assessments", "emoji": True},
                        "action_id": "assign_assessment_button"
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": ":trophy: Leaderboard", "emoji": True},
                        "action_id": "leaderboard_button"
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": ":bust_in_silhouette: Talent Profile", "emoji": True},
                        "action_id": "talent_profile_button"
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": ":gear: Settings", "emoji": True},
                        "action_id": "configurations_button"
                    }
                ]
            },
            {"type": "divider"}
        ])
    else:
        # Engineer buttons
        blocks.extend([
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": ":clipboard: My Assignments", "emoji": True},
                        "style": "primary",
                        "action_id": "view_assignments_button"
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": ":trophy: Leaderboard", "emoji": True},
                        "action_id": "leaderboard_button"
                    }
                ]
            },
            {"type": "divider"}
        ])
    
    # --- Actionable dashboard stats ---
    # Compute engineers with zero progress
    engineers_at_risk = sum(
        1 for eng_id in app_data["engineers"]
        if any(a.get("engineer_id") == int(eng_id) for a in app_data["assignments"].values())
        and all(a.get("status") != "completed"
                for a in app_data["assignments"].values()
                if a.get("engineer_id") == int(eng_id))
    )
    engineers_stat = f"`{total_engineers}` active"
    if engineers_at_risk and total_engineers:
        engineers_stat += f"\n:warning: {engineers_at_risk} at 0%"

    modules_stat = f"`{total_modules}` available"
    unassigned_modules = total_modules - len(set(
        str(a.get("module_id")) for a in app_data["assignments"].values()
    ))
    if unassigned_modules > 0:
        modules_stat += f"\n:new: {unassigned_modules} unassigned"

    assignments_stat = f"`{total_assignments}` total"
    in_progress_count = sum(1 for a in app_data["assignments"].values() if a.get("status") == "in_progress")
    if in_progress_count:
        assignments_stat += f"\n:arrows_counterclockwise: {in_progress_count} in progress"

    completion_label = _completion_label(completion_rate, total_assignments)

    blocks.extend([
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*:bar_chart: Dashboard*"
            }
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*:busts_in_silhouette: Engineers*\n{engineers_stat}"},
                {"type": "mrkdwn", "text": f"*:books: Modules*\n{modules_stat}"},
                {"type": "mrkdwn", "text": f"*:pencil: Assignments*\n{assignments_stat}"},
                {"type": "mrkdwn", "text": f"*:checkered_flag: Completion*\n{completion_label}"}
            ]
        }
    ])
    
    blocks.append({"type": "divider"})
    
    # Engineer progress summary for admins - with enhanced design
    if user_is_admin:
        blocks.extend([
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "👥 Team Progress",
                    "emoji": True
                }
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": "Track individual engineer progress and send reminders"
                    }
                ]
            }
        ])
        
        # Build engineer summary data
        engineer_summary = []
        for eng_id, eng_data in app_data["engineers"].items():
            eng_assignments = [a for assign_id, a in app_data["assignments"].items() 
                             if a.get("engineer_id") == int(eng_id)]
            
            if eng_assignments:
                total = len(eng_assignments)
                completed = len([a for a in eng_assignments if a.get("status") == "completed"])
                in_progress = len([a for a in eng_assignments if a.get("status") == "in_progress"])
                assigned = len([a for a in eng_assignments if a.get("status") == "assigned"])
                incomplete = total - completed
                
                # Check ping acknowledgment
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
        
        engineer_summary.sort(key=lambda x: x["incomplete"], reverse=True)
        
        if engineer_summary:
            dropdown_options = [{
                "text": {
                    "type": "plain_text",
                    "text": f"{eng['name']} - {eng['completed']}/{eng['total']} complete",
                    "emoji": True
                },
                "value": eng["id"]
            } for eng in engineer_summary]
            
            if not selected_engineer_id and engineer_summary:
                selected_engineer_id = engineer_summary[0]["id"]
            
            dropdown_block = {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*Select an engineer:*"
                },
                "accessory": {
                    "type": "static_select",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "Choose engineer...",
                        "emoji": True
                    },
                    "options": dropdown_options,
                    "action_id": "select_engineer_progress"
                }
            }
            
            if selected_engineer_id:
                for eng in engineer_summary:
                    if eng["id"] == selected_engineer_id:
                        dropdown_block["accessory"]["initial_option"] = {
                            "text": {
                                "type": "plain_text",
                                "text": f"{eng['name']} - {eng['completed']}/{eng['total']} complete",
                                "emoji": True
                            },
                            "value": eng["id"]
                        }
                        break
            
            blocks.append(dropdown_block)
            
            # Show selected engineer details with enhanced styling
            if selected_engineer_id:
                selected_eng = next((eng for eng in engineer_summary if eng["id"] == selected_engineer_id), None)
                
                if selected_eng:
                    completion_rate = (selected_eng["completed"] / selected_eng["total"] * 100) if selected_eng["total"] > 0 else 0
                    # All active teams when no end date, so both teams' data is visible
                    selected_eng_data = app_data["engineers"].get(selected_engineer_id, {})
                    active = get_active_tenures(selected_eng_data)
                    if len(active) > 1:
                        team_labels = [t.get("team", "unassigned").replace("_", " ").title() for t in active]
                        team_end = f"*Current teams:* {', '.join(team_labels)}  ·  _Ongoing_"
                    elif active:
                        t = active[0]
                        team_label = t.get("team", "unassigned").replace("_", " ").title()
                        end_date_str = (t.get("end_date") or "")[:10]
                        team_end = f"*Current team:* {team_label}  ·  *End date:* {end_date_str or '_Ongoing_'}"
                    else:
                        team_end = f"*Current team:* {get_team(selected_eng_data).replace('_', ' ').title()}  ·  _Ongoing_"
                    # Enhanced progress bar
                    filled = int(completion_rate / 10)
                    empty = 10 - filled
                    progress_bar = "🟦" * filled + "⬜" * empty
                    # Status with color coding
                    status_line = f"✅ `{selected_eng['completed']}` Completed  •  " \
                                f"🔄 `{selected_eng['in_progress']}` In Progress  •  " \
                                f"📝 `{selected_eng['assigned']}` Assigned"
                    # Acknowledgment status
                    ack_display = ""
                    if selected_eng["ack_status"] == "acknowledged":
                        ack_display = f"\n🔔 *Reminder Acknowledged* ({selected_eng['ack_timestamp'][:10]})"
                    elif selected_eng["ack_status"] == "pending":
                        ack_display = f"\n⏳ *Reminder Sent* (awaiting response)"
                    details_block = {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*📊 {selected_eng['name']}'s Progress*\n{team_end}\n\n" \
                                   f"{progress_bar} `{completion_rate:.0f}%`\n\n" \
                                   f"{status_line}{ack_display}"
                        }
                    }
                    
                    blocks.append(details_block)
                    # Actions: Ping and/or Set end date (engineer profile)
                    action_buttons = []
                    if selected_eng["incomplete"] > 0:
                        pb = {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "📍 Send Reminder" if selected_eng["ack_status"] != "acknowledged" else "📍 Remind Again", "emoji": True},
                            "action_id": f"ping_engineer_{selected_eng['id']}"
                        }
                        if selected_eng["ack_status"] != "acknowledged":
                            pb["style"] = "primary"
                        action_buttons.append(pb)
                    if get_active_tenures(app_data["engineers"].get(selected_engineer_id, {})):
                        action_buttons.append({
                            "type": "button",
                            "text": {"type": "plain_text", "text": "📅 Set end date", "emoji": True},
                            "action_id": "set_end_date_button",
                            "value": str(selected_engineer_id)
                        })
                    if action_buttons:
                        blocks.append({"type": "actions", "elements": action_buttons})
        else:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": ":wave: *Get started* — add engineers and assign modules to see progress here."
                }
            })
    
    # Engineer dashboard section — learning path visualization
    if engineer:
        blocks.extend([
            {"type": "divider"},
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": ":runner: My Learning Path",
                    "emoji": True
                }
            }
        ])

        # Get all assignments
        engineer_assignments = [a for assign_id, a in app_data["assignments"].items()
                               if a.get("engineer_id") == int(engineer["id"])]

        if engineer_assignments:
            completed_count = len([a for a in engineer_assignments if a.get("status") == "completed"])
            total_count = len(engineer_assignments)
            progress_percent = int((completed_count / total_count) * 100) if total_count > 0 else 0

            # Team info
            active = get_active_tenures(engineer)
            if len(active) > 1:
                team_labels = [t.get("team", "unassigned").replace("_", " ").title() for t in active]
                team_end_line = f"*Current teams:* {', '.join(team_labels)} · _Ongoing_"
            elif active:
                t = active[0]
                team_label = t.get("team", "unassigned").replace("_", " ").title()
                end_date_str = (t.get("end_date") or "")[:10]
                team_end_line = f"*Current team:* {team_label}"
                if end_date_str:
                    team_end_line += f" · *End date:* {end_date_str}"
                else:
                    team_end_line += " · _Ongoing_"
            else:
                team_end_line = f"*Current team:* {get_team(engineer).replace('_', ' ').title()} · _Ongoing_"

            # Compact progress summary
            completion_label = _completion_label(progress_percent, total_count)
            summary, active_buttons, completed_text = _build_path_summary(engineer_assignments, app_data)

            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{engineer.get('name', 'Unknown')}*  ·  {team_end_line}\n{completion_label}  ({completed_count}/{total_count} modules)\n{summary}"
                }
            })

            # Completed modules (compact strikethrough list)
            if completed_text:
                blocks.append({
                    "type": "context",
                    "elements": [{"type": "mrkdwn", "text": completed_text}]
                })

            # Clickable buttons for current + next modules
            if active_buttons:
                has_active = any(
                    _effective_status(a) in ("in_progress", "assigned") for a in engineer_assignments
                    if _effective_status(a) != "completed"
                )
                label = ":arrow_forward: *Continue your path:*" if has_active else ":point_right: *Up next:*"
                blocks.append({
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": label}
                })
                blocks.append({"type": "actions", "elements": active_buttons})

            # Motivational nudge
            remaining = total_count - completed_count
            if remaining == 1:
                blocks.append({
                    "type": "context",
                    "elements": [{"type": "mrkdwn", "text": ":fire: *1 module to go — you're almost there!*"}]
                })
            elif remaining > 0 and completed_count > 0:
                blocks.append({
                    "type": "context",
                    "elements": [{"type": "mrkdwn", "text": f":muscle: *{remaining} modules remaining* — keep the momentum going!"}]
                })
    
    # Pending unlock requests - enhanced styling
    if pending_requests > 0:
        blocks.extend([
            {"type": "divider"},
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*⏳ Pending Unlock Requests* (`{pending_requests}`)"
                }
            }
        ])
        
        pending_list = [(progress_id, progress_data) for progress_id, progress_data in app_data["progress"].items()
                       if progress_data.get("unlock_requested") and not progress_data.get("unlock_approved")]
        
        for progress_id, request in pending_list[:5]:
            engineer_id = request.get("engineer_id")
            assignment_id = request.get("assignment_id")
            
            engineer_name = "Unknown"
            if engineer_id and str(engineer_id) in app_data["engineers"]:
                engineer_name = app_data["engineers"][str(engineer_id)].get("name", "Unknown")
            
            module_name = "Unknown"
            if assignment_id and str(assignment_id) in app_data["assignments"]:
                assignment = app_data["assignments"][str(assignment_id)]
                module_id = assignment.get("module_id")
                if module_id and str(module_id) in app_data["modules"]:
                    module_name = app_data["modules"][str(module_id)].get("name", "Unknown")
            
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"👤 *{engineer_name}*\n📚 Requesting: _{module_name}_"
                },
                "accessory": {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "✅ Approve",
                        "emoji": True
                    },
                    "style": "primary",
                    "action_id": f"approve_unlock_{progress_id}"
                }
            })
    
    # --- Trailhead Profile ---
    if engineer and engineer.get("trailhead_username"):
        th_username = engineer["trailhead_username"]
        th_data = fetch_trailhead_profile(th_username)
        if th_data:
            # Normalize: if stored value is already a full URL, use it; otherwise build one
            if th_username.startswith("http"):
                profile_url = th_username.strip().rstrip("/")
            else:
                profile_url = f"https://www.salesforce.com/trailblazer/{th_username}"
            certs = th_data.get("certifications", [])
            active_certs = [c for c in certs if not c.get("expired")]
            points_display = f"{th_data['points']:,}"

            blocks.extend([
                {"type": "divider"},
                {
                    "type": "header",
                    "text": {"type": "plain_text", "text": ":mountain: Trailhead Profile", "emoji": True}
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": f"*:star: Rank*\n{th_data['rank']}"},
                        {"type": "mrkdwn", "text": f"*:medal: Badges*\n{th_data['badges']}"},
                        {"type": "mrkdwn", "text": f"*:gem: Points*\n{points_display}"},
                        {"type": "mrkdwn", "text": f"*:hiking_boot: Trails*\n{th_data['trails']}"},
                    ]
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": f"*:trophy: Superbadges*\n{th_data['superbadges']}"},
                        {"type": "mrkdwn", "text": f"*:scroll: Certifications*\n{len(active_certs)} active"},
                    ]
                },
            ])

            # Show top 5 certifications
            if active_certs:
                cert_lines = []
                for c in active_certs[:5]:
                    status_icon = ":white_check_mark:" if c["status"] == "Active" else ":warning:"
                    cert_lines.append(f"{status_icon} {c['title']}  _({c['status']})_")
                if len(active_certs) > 5:
                    cert_lines.append(f"_+{len(active_certs) - 5} more_")
                blocks.append({
                    "type": "context",
                    "elements": [{"type": "mrkdwn", "text": "\n".join(cert_lines)}]
                })

            blocks.append({
                "type": "actions",
                "elements": [{
                    "type": "button",
                    "text": {"type": "plain_text", "text": ":mountain: View Full Profile", "emoji": True},
                    "url": profile_url,
                    "action_id": "open_trailhead_profile"
                }]
            })

    # --- Recent Wins / Activity Feed ---
    recent_events = _build_recent_activity(app_data)
    if recent_events:
        blocks.extend([
            {"type": "divider"},
            {
                "type": "header",
                "text": {"type": "plain_text", "text": ":trophy: Recent Wins", "emoji": True}
            }
        ])

        for event in recent_events:
            ts = event["timestamp"][:10] if len(event["timestamp"]) >= 10 else event["timestamp"]
            blocks.append({
                "type": "context",
                "elements": [
                    {"type": "mrkdwn", "text": f"{event['text']}  ·  {ts}"}
                ]
            })

        # Team summary stat
        total_completed = len([a for a in app_data["assignments"].values() if a.get("status") == "completed"])
        if total_completed > 0:
            # Count completions in last 7 days
            seven_days_ago = (datetime.now() - timedelta(days=7)).isoformat()
            recent_count = sum(
                1 for a in app_data["assignments"].values()
                if a.get("status") == "completed"
                and (a.get("completed_at") or "") >= seven_days_ago
            )
            if recent_count > 0:
                blocks.append({
                    "type": "context",
                    "elements": [
                        {"type": "mrkdwn", "text": f":fire: *{recent_count} module{'s' if recent_count != 1 else ''} completed this week* across the team"}
                    ]
                })

    # Footer
    blocks.extend([
        {"type": "divider"},
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": ":bulb: *Tip:* Re-open the Home tab to refresh  |  :mortar_board: Keep learning!"
                }
            ]
        }
    ])
    
    return {
        "type": "home",
        "blocks": blocks
    }

