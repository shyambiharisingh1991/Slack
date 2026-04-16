# Heroku Deployment Guide

## Quick Setup Commands

```bash
# 1. Create Heroku app
heroku create your-learning-management-app

# 2. Add PostgreSQL addon
heroku addons:create heroku-postgresql:mini

# 3. Set environment variables
heroku config:set SLACK_BOT_TOKEN=xoxb-your-bot-token-here
heroku config:set SLACK_SIGNING_SECRET=your-signing-secret-here

# 4. Deploy the app
git add .
git commit -m "Initial deployment"
git push heroku main

# 5. Run database migrations (optional, done automatically via Procfile)
heroku run python seed_data.py
```

## Slack App Configuration

After deployment, update your Slack app settings:

1. **Event Subscriptions**:
   - Request URL: `https://your-app-name.herokuapp.com/slack/events`

2. **Slash Commands** (create each one):
   - `/progress` → `https://your-app-name.herokuapp.com/slack/events`
   - `/my-assignments` → `https://your-app-name.herokuapp.com/slack/events`
   - `/request-unlock` → `https://your-app-name.herokuapp.com/slack/events`
   - `/leaderboard` → `https://your-app-name.herokuapp.com/slack/events`

3. **Interactive Components**:
   - Request URL: `https://your-app-name.herokuapp.com/slack/events`

4. **App Home**:
   - Enable Home Tab
   - Enable Messages Tab

## Required OAuth Scopes

Bot Token Scopes:
- `app_mentions:read`
- `channels:read`
- `chat:write`
- `commands`
- `users:read`
- `users:read.email`
- `im:write`

## Testing

After deployment:
1. Install app to your workspace
2. Visit the Home tab
3. Try adding an engineer
4. Test slash commands
5. Assign modules and track progress
