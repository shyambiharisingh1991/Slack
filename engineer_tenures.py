"""
Engineer tenures: one profile per person, multiple team stints with start/end dates.
Backward compatible with engineers that have team/geo/onboarding_plan at top level (legacy).
"""
from datetime import date, datetime


def _ensure_tenures(engineer):
    """If engineer has legacy team/geo/onboarding_plan but no tenures, create one tenure from them."""
    if engineer.get("tenures") is not None:
        return
    team = engineer.get("team", "unassigned")
    geo = engineer.get("geo", "unassigned")
    plan = engineer.get("onboarding_plan", "custom")
    created = engineer.get("created_at") or ""
    start_date = created[:10] if isinstance(created, str) and len(created) >= 10 else date.today().isoformat()
    engineer["tenures"] = [
        {
            "team": team,
            "geo": geo,
            "onboarding_plan": plan,
            "start_date": start_date,
            "end_date": None,
        }
    ]


def get_current_tenure(engineer):
    """
    Return the current tenure (last one with end_date is None or in the future).
    Ensures engineer has tenures (migrates from legacy team/geo/onboarding_plan).
    """
    _ensure_tenures(engineer)
    tenures = engineer.get("tenures") or []
    today = date.today().isoformat()
    current = None
    for t in tenures:
        end = t.get("end_date")
        if end is None or end >= today:
            current = t
    return current or (tenures[-1] if tenures else None)


def get_active_tenures(engineer):
    """
    Return all tenures that are currently active (end_date is None or in the future).
    Use for Home tab when showing "all current teams" so no team's data is overridden.
    """
    _ensure_tenures(engineer)
    tenures = engineer.get("tenures") or []
    today = date.today().isoformat()
    return [t for t in tenures if t.get("end_date") is None or t.get("end_date") >= today]


def get_all_tenures(engineer):
    """
    Return all tenures in order (for reports). Ensures engineer has tenures.
    """
    _ensure_tenures(engineer)
    return list(engineer.get("tenures") or [])


def get_team(engineer):
    """Current team for display (backward compat)."""
    t = get_current_tenure(engineer)
    return t["team"] if t else engineer.get("team", "unassigned")


def get_geo(engineer):
    """Current geo for display."""
    t = get_current_tenure(engineer)
    return t["geo"] if t else engineer.get("geo", "unassigned")


def get_onboarding_plan(engineer):
    """Current onboarding plan for display."""
    t = get_current_tenure(engineer)
    return t["onboarding_plan"] if t else engineer.get("onboarding_plan", "custom")


def migrate_engineers_to_tenures(app_data):
    """Ensure every engineer has a tenures list (from legacy team/geo/onboarding_plan). Modifies app_data in place. Returns True if any was updated."""
    updated = False
    for eng in (app_data.get("engineers") or {}).values():
        if eng.get("tenures") is None and (eng.get("team") is not None or eng.get("geo") is not None or eng.get("onboarding_plan") is not None):
            _ensure_tenures(eng)
            updated = True
    return updated


def add_tenure(engineer, team, geo, onboarding_plan, start_date_str, end_previous_on=None):
    """
    End the current tenure (set end_date to end_previous_on or start_date - 1 day)
    and append a new tenure. Modifies engineer in place.
    """
    _ensure_tenures(engineer)
    tenures = engineer["tenures"]
    if tenures:
        last = tenures[-1]
        if last.get("end_date") is None and end_previous_on:
            last["end_date"] = end_previous_on
        elif last.get("end_date") is None and start_date_str:
            try:
                start_d = datetime.strptime(start_date_str, "%Y-%m-%d").date()
                from datetime import timedelta
                end_previous_on = (start_d - timedelta(days=1)).isoformat()
                last["end_date"] = end_previous_on
            except Exception:
                last["end_date"] = date.today().isoformat()
    engineer["tenures"].append({
        "team": team,
        "geo": geo,
        "onboarding_plan": onboarding_plan,
        "start_date": start_date_str,
        "end_date": None,
    })


def set_tenure_end_date(engineer, tenure_index, end_date_str):
    """
    Set end date for a specific tenure (configurable from engineer profile in Slack).
    Validates end_date >= start_date for that tenure. Modifies engineer in place.
    Returns (True, None) on success, (False, "error message") on validation failure.
    """
    _ensure_tenures(engineer)
    tenures = engineer.get("tenures") or []
    if tenure_index < 0 or tenure_index >= len(tenures):
        return False, "Invalid tenure"
    t = tenures[tenure_index]
    start_date = (t.get("start_date") or "")[:10]
    if not start_date:
        return False, "Tenure has no start date"
    try:
        end_d = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        start_d = datetime.strptime(start_date, "%Y-%m-%d").date()
        if end_d < start_d:
            return False, f"End date must be on or after start date ({start_date})"
    except ValueError:
        return False, "Invalid date format (use YYYY-MM-DD)"
    t["end_date"] = end_date_str
    return True, None
