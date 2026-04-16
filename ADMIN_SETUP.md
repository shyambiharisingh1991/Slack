# Admin Access Control Setup

This document explains how to configure role-based access control (RBAC) for the Learning Management System.

## Overview

The system has two user types:
- **Admins/Managers**: Can add engineers, assign modules, view reports, and manage configurations
- **Engineers**: Can only view their assignments and access the leaderboard

## Setup Methods

### Method 1: Environment Variable (Recommended for Initial Setup)

Set the `ADMIN_USER_IDS` environment variable with comma-separated Slack user IDs.

#### On Heroku:

```bash
heroku config:set ADMIN_USER_IDS="U01ABC123,U02DEF456,U03GHI789" --app your-app-name
```

#### Locally (in .env file):

```bash
ADMIN_USER_IDS=U01ABC123,U02DEF456,U03GHI789
```

#### How to Find Slack User IDs:

1. **In Slack Desktop/Web**:
   - Click on someone's profile
   - Click "More" → "Copy member ID"

2. **From Slack API**:
   - Go to your app's Event Subscriptions
   - Look at incoming events for `user_id` field

3. **Test with yourself**:
   - Add yourself first, then check the logs when you interact with the app
   - Look for lines like: `User ID: U01ABC123`

### Method 2: Database Role Field

When adding engineers through the app, you can set their role to "admin" or "manager" in the database.

**Current implementation**: Engineers added through the "Add Engineer" modal are assigned the role "engineer" by default. To make someone an admin:

1. Use Method 1 (environment variable) initially
2. Future enhancement: Add an admin UI to promote users to admin/manager roles

## Admin Features

Once configured as an admin, users will see these buttons on the Home page:

- ➕ **Add New Engineer** - Register new team members
- 📚 **Assign Module** - Assign training modules to engineers
- 📋 **Assessments** - Assign assessments to engineers
- 📊 **View Detailed Report** - Generate comprehensive PDF reports
- 🏆 **Leaderboard** - View team rankings
- ⚙️ **Configurations** - Manage modules, assessments, and notifications

## Non-Admin Experience

Engineers (non-admins) will only see:

- 🏆 **Leaderboard** - View team rankings
- 📋 **View My Assignments** - Access their assigned modules and assessments
- Their personal assignment dashboard

## Security

- All sensitive admin endpoints include authorization checks
- Attempting to access admin features without permission results in a "Access Denied" message
- Admin status is checked on EVERY action, not just UI visibility

## Testing

To test the admin setup:

1. Set your Slack user ID as an admin using Method 1
2. Restart the app (Heroku: `heroku restart --app your-app-name`)
3. Open the Slack app Home tab
4. You should see all 6 admin buttons
5. Test with another user who is NOT in the admin list - they should only see 2 buttons

## Troubleshooting

### "I don't see admin buttons"

1. **Check environment variable is set**:
   ```bash
   heroku config --app your-app-name | grep ADMIN_USER_IDS
   ```

2. **Verify your Slack user ID** is in the list

3. **Restart the app** after changing environment variables:
   ```bash
   heroku restart --app your-app-name
   ```

4. **Clear Slack cache**: Close and reopen Slack, or try in a different browser

### "I get 'Access Denied' errors"

- Your user ID is not in the `ADMIN_USER_IDS` environment variable
- The environment variable wasn't loaded (try restarting the app)
- Check Heroku logs for the actual user ID being checked:
  ```bash
  heroku logs --tail --app your-app-name
  ```

## Future Enhancements

Planned features:
- Admin UI to promote/demote users
- Role hierarchy (Super Admin > Manager > Engineer)
- Permission groups (e.g., "can assign modules" vs "can generate reports")
- Audit log of admin actions

## Support

If you need help setting up admin access, check the Heroku logs:

```bash
heroku logs --tail --app your-app-name
```

Look for lines containing "admin" or "authorization" for debugging information.

