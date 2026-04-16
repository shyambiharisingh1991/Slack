# Slack App Setup Guide

## 🔧 Step-by-Step Configuration

Your Heroku app is running perfectly at: `https://cloudsuccesslevelup-472fdd611c95.herokuapp.com/`

Follow these steps to configure your Slack app:

### 1. **Go to Your Slack App Dashboard**
- Visit: https://api.slack.com/apps
- Select your Learning Management app

### 2. **Configure Event Subscriptions**
- Go to **"Event Subscriptions"** in the left sidebar
- Toggle **"Enable Events"** to ON
- **Request URL**: `https://cloudsuccesslevelup-472fdd611c95.herokuapp.com/slack/events`
- Wait for the green checkmark ✅ (this confirms Slack can reach your app)

**Subscribe to Bot Events:**
- Add these events:
  - `app_home_opened` (Required for Home tab)
  - `message.channels` (Optional)

### 3. **Configure App Home**
- Go to **"App Home"** in the left sidebar
- **Enable Home Tab**: ✅ ON
- **Enable Messages Tab**: ✅ ON (optional)

### 4. **Configure Interactive Components**
- Go to **"Interactivity & Shortcuts"** in the left sidebar
- Toggle **"Interactivity"** to ON
- **Request URL**: `https://cloudsuccesslevelup-472fdd611c95.herokuapp.com/slack/events`

### 5. **Configure OAuth Scopes**
- Go to **"OAuth & Permissions"** in the left sidebar
- Under **"Bot Token Scopes"**, add these scopes:
  - `app_mentions:read`
  - `channels:read`
  - `chat:write`
  - `commands`
  - `users:read`
  - `users:read.email`
  - `im:write`

### 6. **Install/Reinstall App to Workspace**
- Go to **"Install App"** in the left sidebar
- Click **"Reinstall to Workspace"** (if already installed)
- Or **"Install to Workspace"** (if first time)
- Authorize the app

### 7. **Test the Home Tab**
- Open Slack
- Go to your **Apps** section in the sidebar
- Click on your **Learning Management** app
- Click the **"Home"** tab
- You should see the dashboard with buttons!

## 🐛 Troubleshooting

### If Home Tab Still Doesn't Load:

1. **Check Event URL Verification:**
   - The Request URL should show a green checkmark ✅
   - If red ❌, check the URL is exactly: `https://cloudsuccesslevelup-472fdd611c95.herokuapp.com/slack/events`

2. **Check App Installation:**
   - Make sure you clicked "Reinstall to Workspace" after adding scopes
   - The app needs to be reinstalled whenever you change scopes

3. **Check Heroku Logs:**
   ```bash
   heroku logs --tail -a cloudsuccesslevelup
   ```
   Look for any errors when you try to access the Home tab

4. **Verify Bot Token:**
   - Make sure your `SLACK_BOT_TOKEN` starts with `xoxb-`
   - Verify it's set correctly in Heroku config

### If You See "This app doesn't have a home":
- Make sure **"Enable Home Tab"** is turned ON in App Home settings
- Make sure you have the `app_home_opened` event subscribed

### If Buttons Don't Work:
- Verify **Interactive Components** is enabled
- Check that the Request URL is correct

## 📝 Create Slash Commands (Optional)

Go to **"Slash Commands"** and create these:

1. **Command**: `/progress`
   - **Request URL**: `https://cloudsuccesslevelup-472fdd611c95.herokuapp.com/slack/events`
   - **Description**: View your learning progress

2. **Command**: `/my-assignments`
   - **Request URL**: `https://cloudsuccesslevelup-472fdd611c95.herokuapp.com/slack/events`
   - **Description**: List your current assignments

3. **Command**: `/request-unlock`
   - **Request URL**: `https://cloudsuccesslevelup-472fdd611c95.herokuapp.com/slack/events`
   - **Description**: Request to unlock next module

4. **Command**: `/leaderboard`
   - **Request URL**: `https://cloudsuccesslevelup-472fdd611c95.herokuapp.com/slack/events`
   - **Description**: View team leaderboard

## ✅ Success Indicators

You'll know everything is working when:
- ✅ Event Subscriptions shows green checkmark
- ✅ Home tab loads with your dashboard
- ✅ Buttons respond when clicked
- ✅ You can add engineers and assign modules
- ✅ Slash commands work (if created)

## 🔍 Quick Test

1. Open the app's Home tab in Slack
2. Click **"Add New Engineer"** button
3. A modal should open
4. If this works, your app is fully configured! 🎉
