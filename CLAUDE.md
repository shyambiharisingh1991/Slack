# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Slack bot application for managing engineering training programs, tracking progress, and facilitating team learning. Built with Python 3.11, Slack Bolt, Flask, and PostgreSQL. Deployed to Heroku. Integrates with the Trailhead GraphQL API for live profile data.

## Development Commands

```bash
# Setup
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Create .env from .env.example and fill in SLACK_BOT_TOKEN, SLACK_SIGNING_SECRET, ADMIN_USER_IDS

# Run locally
python app.py
# Runs on port 3000 by default (configurable via PORT env var)

# Deploy to Heroku (note: local branch is master, Heroku remote expects main)
git push heroku master:main

# View Heroku logs
heroku logs --tail
```

There are no automated tests.

## Architecture

### Directory Structure Warning

The `cloudsuccesslevelup/` subdirectory is a **legacy copy** of the codebase. Do NOT edit files in that directory. All active code lives at the repository root (`app.py`, `handlers/`, `ui/`, etc.).

### Application Entry Point

**app.py** initializes Flask + Slack Bolt, registers all handlers, and manages the global data store. Heroku runs via `Procfile` (`gunicorn app:flask_app`). Python version is specified in `.python-version` (3.11).

The app boots even without Slack credentials (returns 503 to Slack events until configured).

### Handler Registration Pattern

All handlers follow the same pattern:
1. Import handler module in `app.py`
2. Call `register_*()` passing `app`, `get_app_data`, `save_data` callbacks
3. Handlers use these callbacks to read/write data

### Handlers (`handlers/`)
- **actions.py**: Button click handlers. Every admin action checks `is_admin(user_id, app_data)`. URL-opening buttons (`open_trailhead_profile`, `open_trailhead_module`, `open_learning_materials`) have ack-only handlers registered at the end of the file.
- **views.py**: Modal submission handlers. Contains `migrate_existing_assignments()` which runs on startup to add locking to legacy assignments.
- **events.py**: Slack event handlers (`app_home_opened` refreshes home tab).
- **assessment_handlers.py**: Assessment-specific interactions (quiz taking, grading).

### UI Components (`ui/`)
- **home.py**: Home tab view with personalized greeting, attention alerts, grouped admin buttons, actionable dashboard stats, compact learning path with clickable module buttons, live Trailhead profile section, and Recent Wins activity feed.
- **modals.py**: Modal builders for engineer creation (includes Trailhead username field), module assignment, report generation
- **module_modal.py**: Module start modals with "Open in Trailhead" button when module has a `trailhead_url`. Special handling for March Accreditation video.
- **module_modals.py**: Module create/edit modal (includes optional Trailhead URL field)
- **assessment_modal.py**: Assessment/quiz modals with question display and results
- **assessment_editor.py**: Assessment editing UI
- **assessment_modals.py**: Additional assessment modal builders
- **notification_modals.py**: Notification-related modals
- **search_modal.py**: Global search across engineers, modules, assignments
- **configurations.py**: Admin configuration screens

### Root-Level Business Logic
- **auth.py**: Role-based access control. `is_admin(user_id, app_data)` checks env var + DB role. Also provides a `require_admin` decorator for handlers.
- **engineer_tenures.py**: Multi-tenure tracking (one engineer, multiple team stints). Always use `get_team(engineer)`, `get_geo(engineer)`, `get_current_tenure(engineer)` — never access `engineer["team"]` directly.
- **trailhead.py**: Fetches live Trailhead profile data (rank, badges, points, trails, superbadges, certifications) from the Trailhead GraphQL API (`profile.api.trailhead.com/graphql`). Normalizes usernames from full URLs automatically.
- **pdf_generator.py**: ReportLab-based PDF generation with progress rings, executive summaries, completion timelines, overdue indicators, and Trailhead readiness sections.
- **db_storage.py**: PostgreSQL interface. Stores all data as JSONB in `app_data` table (single row, id=1). Falls back to file storage if `DATABASE_URL` not set.
- **storage.py**: File-based storage fallback using `app_data.json`.

### Data Structure

All data lives in a single JSONB column:
```python
{
  "engineers": {},      # key: string id, includes slack_user_id, role, tenures[], trailhead_username
  "modules": {},        # key: string id, optional trailhead_url field
  "assignments": {},    # key: string id, includes sequence_order, unlocked, completed_at
  "assessments": {},    # key: string id, questions can be int (legacy) or array
  "progress": {},       # key: string id
  "next_ids": {}        # auto-increment counters per entity type
}
```

## Key Patterns

### Data Access
Always reload from DB before modifying:
```python
app_data = get_app_data()  # Always reloads from DB
# Modify app_data...
save_data(app_data)  # Persists to DB
```

### Authorization
All admin actions must check authorization:
```python
from auth import is_admin
user_id = body["user"]["id"]
if not is_admin(user_id, app_data):
    client.chat_postMessage(channel=user_id, text="Access Denied...")
    return
```

### Assignment Status
Use `_effective_status(assign)` from `ui/home.py` to determine display status. An assignment with `status="locked"` but `unlocked=True` is treated as ready/assigned. Legacy assignments may lack `type` field — treat missing type as module.

### Adding a New Modal
1. Create modal builder function in appropriate `ui/` file
2. Add button action handler in `handlers/actions.py`
3. Add view submission handler in `handlers/views.py`
4. Add authorization check if admin-only

### Adding a New Data Entity
1. Add entity to default data in both `storage.py` and `db_storage.py`
2. Add `next_ids` counter for the entity
3. Create UI modals and handlers for all interactions

## Slash Commands

- `/progress` — View your current progress
- `/my-assignments` — List all your assignments
- `/request-unlock` — Request to unlock next module
- `/leaderboard` — View team leaderboard

## Special Features

### Personalized Home Tab
Time-aware greeting ("Good morning, Shyam"), attention alerts (overdue modules, zero-progress engineers, pending unlocks), grouped admin buttons (primary/secondary rows), actionable dashboard stats with contextual sub-labels.

### Learning Path Visualization
Compact summary showing status counts + up to 3 clickable module buttons (uses `start_module_{id}` action). In-progress modules get primary button style. Completed modules shown as strikethrough.

### Trailhead Integration
Engineers can link their Trailhead profile (`trailhead_username` field). Modules can have a `trailhead_url`. The home tab fetches live data from `profile.api.trailhead.com/graphql` showing rank, badges, points, trails, superbadges, and certifications. PDF reports include a "Trailhead Readiness" section. The `trailhead.py` module handles API calls and normalizes usernames from full URLs.

### Recent Wins Activity Feed
Shows recent module completions across the team with weekly completion count.

### Executive PDF Reports
Progress ring visualization, narrative executive summary, completion timeline with pace calculation, active/upcoming modules with days-until-due and overdue flags, color-coded assignment log, Trailhead readiness with full certification table.

### March Accreditation Module
Hardcoded module ID handling in `ui/module_modal.py`. Plays video in same modal via Slack video block. Requires `links.embed:write` scope and video domain in Unfurl Domains.

### Sequential Module Unlocking
Assignments have `sequence_order` and `unlocked` fields. Only the first module is unlocked initially; completing a module unlocks the next.

### Assessment System
Assessment `questions` can be int (legacy) or array of question objects — always normalize to array format.

## Environment Variables

Required:
- `SLACK_BOT_TOKEN`: Bot token (xoxb-...)
- `SLACK_SIGNING_SECRET`: Signing secret

Optional:
- `ADMIN_USER_IDS`: Comma-separated Slack user IDs with admin access
- `DATABASE_URL`: PostgreSQL connection string (Heroku auto-sets this)
- `PORT`: Server port (default: 3000)
- `MARCH_ACCREDITATION_VIDEO_URL`: YouTube URL for March module video

## Slack App Configuration

Required scopes: `app_mentions:read`, `channels:read`, `chat:write`, `commands`, `users:read`, `users:read.email`, `im:write`, `links.embed:write` (for video features).

Event subscriptions: `app_home_opened`. Interactive components and slash commands point to: `/slack/events`.

## Known Constraints

- No automated tests
- Single JSONB column stores all data (not normalized relational tables)
- File storage fallback doesn't support concurrent access
- March Accreditation module has hardcoded handling throughout codebase
- Assessment questions can be int (legacy) or array (new) — always normalize
- Trailhead API is public but undocumented — may change without notice
- `cloudsuccesslevelup/` directory is stale — do not edit
