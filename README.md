# Learning Management Slack App

A comprehensive Slack application for managing engineering training programs, tracking progress, and facilitating team learning. Integrates with Salesforce Trailhead for live profile data and certification tracking.

## Features

### 🏠 Personalized Home Tab
- Time-aware greeting ("Good morning, Shyam") with role and date
- Attention alerts: overdue assignments, zero-progress engineers, pending unlock requests
- Grouped quick actions: primary (Add Engineer, Assign Module, Reports) and secondary (Assessments, Leaderboard, Talent Profile, Settings)
- Actionable dashboard stats with contextual sub-labels (e.g., "2 at 0%", "3 unassigned")

### 🏃 Learning Path Visualization
- Compact status summary (completed, in progress, ready, locked counts)
- Up to 3 clickable module buttons to jump directly into modules
- Completed modules shown as strikethrough
- Motivational nudges ("1 module to go — you're almost there!")

### 🏔️ Trailhead Integration
- Link engineer profiles to Trailhead via username or full profile URL
- Live data from Trailhead GraphQL API: rank, badges, points, trails, superbadges
- Certification list with status (Active / Maintenance Due / Expired)
- "View Full Profile" button linking to trailblazer.me
- Optional Trailhead URL on modules — "Open in Trailhead" button in module modal
- Trailhead Readiness section in PDF reports with full certification table

### 🏆 Recent Wins & Activity Feed
- Recent module completions across the team
- Weekly team completion count
- Completion dates and engineer names

### 📊 Executive PDF Reports
- Visual donut progress ring (color-coded by completion %)
- Narrative executive summary ("Shyam has completed 1 of 23 modules...")
- Completion timeline with average pace calculation
- Active & upcoming modules table with days-until-due and overdue flags
- Full assignment log with color-coded rows (green = done, red = overdue)
- Trailhead Readiness section with stats and certification table
- Module, assessment, and overdue report types

### 👥 Engineer Management
- Add new engineers with Slack user linking
- Multi-tenure tracking (team, geo, onboarding plan, start/end dates)
- Optional Trailhead username for profile integration
- Role-based access control (admin, manager, engineer)

### 📚 Module Management
- Create/edit modules with name, description, duration, skills
- Optional Trailhead URL for each module
- Sequential unlocking — completing one module unlocks the next
- "Open Learning Materials" and "Open in Trailhead" buttons in module modal

### 📋 Assessment System
- Quiz and assessment creation with multiple question types
- Per-question video URLs
- Grading and completion tracking

### 🔔 Notifications & Reminders
- Send reminders to engineers with incomplete modules
- Reminder acknowledgment tracking
- Unlock request workflow (engineer requests, admin approves)

### 💬 Slash Commands
- `/progress` — View your current progress
- `/my-assignments` — List all your assignments
- `/request-unlock` — Request to unlock next module
- `/leaderboard` — View team leaderboard

### 🎥 Video Support
- March Accreditation module plays video in Slack modal via video block
- Per-question video URLs in assessments

## Setup Instructions

### 1. Create Slack App
1. Go to [Slack API](https://api.slack.com/apps)
2. Create a new app "Learning Management System"
3. Enable the following features:
   - **Slash Commands**: Add the commands listed above
   - **Interactive Components**: Enable for buttons and modals
   - **Home Tab**: Enable App Home
   - **Bot Token Scopes**: `app_mentions:read`, `channels:read`, `chat:write`, `commands`, `users:read`, `users:read.email`, `im:write`, `links.embed:write`
4. Event subscriptions: `app_home_opened`
5. All interactive endpoints point to: `/slack/events`

### 2. Environment Variables
Create a `.env` file (see `.env.example`):
```
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_SIGNING_SECRET=your-signing-secret
ADMIN_USER_IDS=U01ABC,U02DEF
DATABASE_URL=postgresql://user:pass@host:5432/dbname  # optional, falls back to file storage
```

### 3. Local Development
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
# Runs on port 3000
```

### 4. Heroku Deployment
```bash
heroku login
heroku create your-learning-management-app
heroku addons:create heroku-postgresql:mini
heroku config:set SLACK_BOT_TOKEN=xoxb-... SLACK_SIGNING_SECRET=...
git push heroku master:main
```

Update your Slack app URLs to: `https://your-app-name.herokuapp.com/slack/events`

## Usage Guide

### For Managers
1. **Add Engineers**: Use "Add Engineer" button — link Slack user, assign team/geo, optionally add Trailhead username
2. **Create Modules**: Settings → Create Module — add name, description, optional Trailhead URL
3. **Assign Modules**: Click "Assign Module" — select engineer and module with due date
4. **Monitor Progress**: View dashboard stats, engineer dropdown, and generate PDF reports
5. **Send Reminders**: Click "Send Reminder" on engineers with incomplete modules
6. **Approve Unlocks**: Handle unlock requests from the Home tab

### For Engineers
1. **View Learning Path**: Open Home tab to see your compact learning path with clickable modules
2. **Complete Modules**: Click module button → review materials → "Open in Trailhead" if linked → Mark as Complete
3. **Track Trailhead**: Link your Trailhead profile to see badges, rank, and certifications in the Home tab
4. **View Leaderboard**: Check team rankings and completion rates

## Tech Stack

- **Python 3.11** with Flask and Slack Bolt
- **PostgreSQL** (JSONB storage) with file-based fallback
- **ReportLab** for PDF generation
- **Trailhead GraphQL API** for live profile data
- **Heroku** for deployment (gunicorn)

## Troubleshooting

### Common Issues
1. **Database Connection**: Ensure `DATABASE_URL` is set (Heroku adds it automatically with Postgres addon)
2. **Slack Permissions**: Verify all required scopes are added
3. **Trailhead Profile Not Showing**: The username field accepts both `architects` and `https://www.salesforce.com/trailblazer/architects` — URLs are normalized automatically

### Logs
```bash
heroku logs --tail
heroku logs --source app
```

## License
MIT License - see LICENSE file for details
