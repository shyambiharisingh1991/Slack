# Learning Management Slack App

A comprehensive Slack application for managing engineering training programs, tracking progress, and facilitating team learning.

## Features

### 🏠 Home Tab Dashboard
- Overview of team progress
- Quick access to all management functions
- Pending unlock requests management
- Real-time statistics

### 👥 Engineer Management
- Add new engineers to the system
- Assign roles and permissions
- Link Slack users to engineer profiles

### 📚 Module Assignment
- Assign training modules to engineers
- Set due dates and track deadlines
- Automated notifications

### 📊 Progress Tracking
- Real-time progress updates
- Visual progress bars
- Current section tracking
- Notes and feedback system

### 🏆 Gamification
- Leaderboard with completion rates
- Achievement tracking
- Team progress overview

### 💬 Slash Commands
- `/progress` - View your current progress
- `/my-assignments` - List all your assignments
- `/request-unlock` - Request to unlock next module
- `/leaderboard` - View team leaderboard

## Setup Instructions

### 1. Create Slack App
1. Go to [Slack API](https://api.slack.com/apps)
2. Create a new app "Learning Management System"
3. Enable the following features:
   - **Slash Commands**: Add the commands listed above
   - **Interactive Components**: Enable for buttons and modals
   - **Home Tab**: Enable App Home
   - **Bot Token Scopes**: Add these scopes:
     - `app_mentions:read`
     - `channels:read`
     - `chat:write`
     - `commands`
     - `users:read`
     - `users:read.email`

### 2. Environment Variables
Create a `.env` file with:
```
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_SIGNING_SECRET=your-signing-secret
DATABASE_URL=postgresql://username:password@host:port/database
```

### 3. Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Set up database
python seed_data.py

# Run the app
python app.py
```

### 4. Heroku Deployment

#### Prerequisites
- Heroku account
- Heroku CLI installed
- Git repository

#### Steps
```bash
# Login to Heroku
heroku login

# Create Heroku app
heroku create your-learning-management-app

# Add PostgreSQL addon
heroku addons:create heroku-postgresql:mini

# Set environment variables
heroku config:set SLACK_BOT_TOKEN=xoxb-your-bot-token
heroku config:set SLACK_SIGNING_SECRET=your-signing-secret

# Deploy
git add .
git commit -m "Initial deployment"
git push heroku main
```

#### Configure Slack App URLs
After deployment, update your Slack app configuration:
- **Request URL**: `https://your-app-name.herokuapp.com/slack/events`
- **Slash Commands URLs**: `https://your-app-name.herokuapp.com/slack/events`

### 5. Initial Setup
1. Install the app to your Slack workspace
2. Run the seed script to populate sample modules
3. Add engineers through the Home tab
4. Start assigning modules!

## Database Schema

### Engineers
- Personal information and Slack user mapping
- Role-based permissions
- Creation timestamps

### Modules
- Training content metadata
- Prerequisites and estimated hours
- Categorization (basics, intermediate, advanced)

### Assignments
- Links engineers to modules
- Due dates and status tracking
- Assignment history

### Progress
- Detailed progress tracking
- Section-level granularity
- Unlock request management

### Assessments
- Quiz and project scoring
- Feedback and completion tracking

## Usage Guide

### For Managers
1. **Add Engineers**: Use the "Add New Engineer" button in the Home tab
2. **Assign Modules**: Click "Assign Module" and select engineer and module
3. **Monitor Progress**: View detailed reports and leaderboards
4. **Handle Requests**: Approve unlock requests from the Home tab

### For Engineers
1. **Check Progress**: Use `/progress` command or visit Home tab
2. **View Assignments**: Use `/my-assignments` to see all current tasks
3. **Update Progress**: Click "Update Progress" on assignments
4. **Request Unlocks**: Use `/request-unlock Module Name` when ready to advance

## Customization

### Adding New Modules
Edit `seed_data.py` to add more training modules:
```python
{
    "name": "Your Module Name",
    "description": "Module description",
    "category": "basics|intermediate|advanced",
    "estimated_hours": 40,
    "prerequisites": "[1,2]"  # JSON array of prerequisite module IDs
}
```

### Modifying UI
- Edit `views.py` for Home tab layout
- Modify `handlers.py` for interactive components
- Update `slash_commands.py` for command responses

## Troubleshooting

### Common Issues
1. **Database Connection**: Ensure DATABASE_URL is correctly set
2. **Slack Permissions**: Verify all required scopes are added
3. **URL Configuration**: Check that Heroku URLs match Slack app settings

### Logs
```bash
# View Heroku logs
heroku logs --tail

# Check specific errors
heroku logs --source app
```

## Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License
MIT License - see LICENSE file for details
