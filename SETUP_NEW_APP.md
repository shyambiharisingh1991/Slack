# Setting Up This App for a New Heroku / Slack Instance

This project was copied from the demo Heroku Level Up app. Use this checklist to point it at your new app and URLs.

## 1. Heroku app

- Create or use your Heroku app (e.g. `cloudsuccess-learning-vibe-9aed81e68bcd`).
- Add Postgres: **Resources** → **Find more add-ons** → Heroku Postgres (so `DATABASE_URL` is set).
- In **Settings** → **Config Vars**, set:
  - `SLACK_BOT_TOKEN` – Bot User OAuth Token from your Slack app.
  - `SLACK_SIGNING_SECRET` – Signing Secret from your Slack app.
  - (Optional) `ADMIN_USER_IDS` – comma-separated Slack user IDs for admins.

## 2. Slack app (api.slack.com)

- **OAuth & Permissions**: install to workspace and copy **Bot User OAuth Token** → use as `SLACK_BOT_TOKEN`.
- **Basic Information** → **App Credentials**: copy **Signing Secret** → use as `SLACK_SIGNING_SECRET`.
- **Event Subscriptions**:
  - Enable Events: **On**.
  - Request URL: `https://<your-heroku-app-name>.herokuapp.com/slack/events`  
    (e.g. `https://cloudsuccess-learning-vibe-9aed81e68bcd.herokuapp.com/slack/events`).
  - Subscribe to **bot events** (e.g. `app_home_opened`).
- **Interactivity & Shortcuts**: if you use shortcuts or interactive components, set **Request URL** to the same base URL (e.g. `https://<your-app>.herokuapp.com/slack/events`).
- **App Home**: enable **Home Tab** and optionally “Allow users to send Slash commands and messages from the messages tab”.

## 3. Local development

- Copy `.env.example` to `.env`.
- Fill in `SLACK_BOT_TOKEN` and `SLACK_SIGNING_SECRET` (and optional `ADMIN_USER_IDS`).
- For local DB you can leave `DATABASE_URL` unset; the app falls back to file storage.
- Run: `pip install -r requirements.txt` then `python app.py` (or use the Procfile: `gunicorn app:flask_app`).

## 4. Deploy to Heroku

From this directory:

```bash
git init
git add .
git commit -m "Initial commit - CloudSuccess Learning Vibe"
heroku git:remote -a <your-heroku-app-name>
git push heroku main
```

Then in Heroku **Resources**, ensure the **web** dyno is on (scale to 1).

## 5. Optional: onboarding channel

If you use the “invite to channel” feature, set the channel ID in code:

- In `handlers/views.py` (and any similar handlers), search for `ONBOARDING_CHANNEL_ID = "C09PL7HN3DZ"` and replace with your Slack channel ID (from channel details in Slack).

---

After this, saving the Slack **Request URL** under Event Subscriptions should pass verification (your app responds with the `challenge` parameter), and the app will run on Heroku with your new credentials and URLs.
