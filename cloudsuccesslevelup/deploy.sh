#!/bin/bash

# Heroku Deployment Script for Learning Management Slack App

echo "🚀 Starting deployment to Heroku..."

# Check if Heroku CLI is installed
if ! command -v heroku &> /dev/null; then
    echo "❌ Heroku CLI not found. Please install it first."
    exit 1
fi

# Check if logged in to Heroku
if ! heroku auth:whoami &> /dev/null; then
    echo "🔐 Please log in to Heroku first:"
    heroku login
fi

# Get app name from user
read -p "Enter your Heroku app name (e.g., my-learning-management-app): " APP_NAME

if [ -z "$APP_NAME" ]; then
    echo "❌ App name is required"
    exit 1
fi

# Create Heroku app
echo "📱 Creating Heroku app: $APP_NAME"
heroku create $APP_NAME

# Add PostgreSQL addon
echo "🗄️ Adding PostgreSQL database..."
heroku addons:create heroku-postgresql:mini --app $APP_NAME

# Get environment variables from user
echo "🔧 Setting up environment variables..."
read -p "Enter your SLACK_BOT_TOKEN (xoxb-...): " BOT_TOKEN
read -p "Enter your SLACK_SIGNING_SECRET: " SIGNING_SECRET

if [ -z "$BOT_TOKEN" ] || [ -z "$SIGNING_SECRET" ]; then
    echo "❌ Both Slack tokens are required"
    exit 1
fi

# Set environment variables
heroku config:set SLACK_BOT_TOKEN=$BOT_TOKEN --app $APP_NAME
heroku config:set SLACK_SIGNING_SECRET=$SIGNING_SECRET --app $APP_NAME

# Initialize git if needed
if [ ! -d ".git" ]; then
    echo "📝 Initializing git repository..."
    git init
    git add .
    git commit -m "Initial commit"
fi

# Add Heroku remote
heroku git:remote -a $APP_NAME

# Deploy to Heroku
echo "🚀 Deploying to Heroku..."
git add .
git commit -m "Deploy to Heroku" --allow-empty
git push heroku main

# Show app URL
echo "✅ Deployment complete!"
echo "🌐 Your app is running at: https://$APP_NAME.herokuapp.com"
echo ""
echo "📋 Next steps:"
echo "1. Update your Slack app configuration with:"
echo "   - Request URL: https://$APP_NAME.herokuapp.com/slack/events"
echo "2. Add the required OAuth scopes (see README.md)"
echo "3. Install the app to your workspace"
echo "4. Test the Home tab and slash commands"
echo ""
echo "📖 For detailed setup instructions, see heroku_setup.md"
