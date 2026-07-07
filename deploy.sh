#!/bin/bash

# Hermes Autonomous Agent System - Deployment Script
# This script automates Railway deployment

set -e  # Exit on error

echo "=================================="
echo "Hermes Autonomous Agent System"
echo "Railway Deployment Script"
echo "=================================="
echo ""

# Check if railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI not found!"
    echo ""
    echo "Install it first:"
    echo "  npm install -g @railway/cli"
    echo "  OR"
    echo "  brew install railway"
    exit 1
fi

echo "✓ Railway CLI found"
echo ""

# Check if logged in
if ! railway whoami &> /dev/null; then
    echo "🔐 Please login to Railway..."
    railway login
fi

echo "✓ Logged in to Railway"
echo ""

# Check for required environment variables
echo "Checking required credentials..."

read -p "Do you have a Telegram Bot Token? (y/n): " has_telegram
if [ "$has_telegram" != "y" ]; then
    echo ""
    echo "📱 Create a Telegram bot first:"
    echo "  1. Open Telegram"
    echo "  2. Search for @BotFather"
    echo "  3. Send: /newbot"
    echo "  4. Follow instructions"
    echo "  5. Copy the BOT_TOKEN"
    echo ""
    read -p "Press Enter when you have the token..."
fi

read -p "Enter your Telegram Bot Token: " telegram_token
if [ -z "$telegram_token" ]; then
    echo "❌ Telegram token required!"
    exit 1
fi

read -p "Do you have an Anthropic API key? (y/n): " has_anthropic
if [ "$has_anthropic" != "y" ]; then
    echo ""
    echo "🔑 Get Anthropic API key:"
    echo "  1. Go to: console.anthropic.com"
    echo "  2. Create account / login"
    echo "  3. Generate API key"
    echo ""
    read -p "Press Enter when you have the key..."
fi

read -p "Enter your Anthropic API key: " anthropic_key
if [ -z "$anthropic_key" ]; then
    echo "❌ Anthropic API key required!"
    exit 1
fi

echo ""
echo "✓ Credentials collected"
echo ""

# Check if project exists
if [ ! -f ".railway" ]; then
    echo "🚂 Initializing Railway project..."
    railway init
    echo ""
fi

echo "✓ Railway project initialized"
echo ""

# Add databases
echo "📦 Adding databases..."

echo "Adding PostgreSQL..."
railway add --database postgres || echo "PostgreSQL may already exist"

echo "Adding Redis..."
railway add --database redis || echo "Redis may already exist"

echo ""
echo "✓ Databases added"
echo ""

# Set environment variables
echo "⚙️  Setting environment variables..."

railway variables set TELEGRAM_BOT_TOKEN="$telegram_token"
railway variables set ANTHROPIC_API_KEY="$anthropic_key"

# Set default configuration
railway variables set DAILY_BUDGET="50.0"
railway variables set MAX_NOTIFICATIONS_PER_DAY="3"
railway variables set LOG_LEVEL="INFO"
railway variables set TZ="Europe/Bratislava"

echo ""
echo "✓ Environment variables set"
echo ""

# Deploy
echo "🚀 Deploying to Railway..."
echo "(This may take 2-3 minutes)"
echo ""

railway up

echo ""
echo "✓ Deployment complete!"
echo ""

# Get URL
echo "🌐 Getting your Railway URL..."
railway_url=$(railway status --json | grep -o '"url":"[^"]*"' | cut -d'"' -f4)

if [ -z "$railway_url" ]; then
    echo "⚠️  Could not auto-detect URL. Please get it from:"
    echo "   railway open"
    read -p "Enter your Railway URL: " railway_url
fi

echo "Your app URL: $railway_url"
echo ""

# Set webhook URL
echo "🔗 Setting Telegram webhook..."
railway variables set TELEGRAM_WEBHOOK_URL="$railway_url"

echo ""
echo "🔄 Redeploying with webhook URL..."
railway up

echo ""
echo "=================================="
echo "✅ DEPLOYMENT SUCCESSFUL!"
echo "=================================="
echo ""
echo "Your Hermes Autonomous Agent System is now running!"
echo ""
echo "📱 Test it:"
echo "  1. Open Telegram"
echo "  2. Search for your bot"
echo "  3. Send: /start"
echo ""
echo "📊 Monitor:"
echo "  railway logs --follow"
echo ""
echo "🎯 Next steps:"
echo "  - Wait 5 minutes for first scheduled task"
echo "  - Check logs for 'CRON: Executing' messages"
echo "  - Receive your first notification!"
echo ""
echo "📚 Documentation:"
echo "  - README.md - Full documentation"
echo "  - QUICKSTART.md - Quick reference"
echo "  - DEPLOYMENT.md - Detailed deployment guide"
echo ""
echo "Need help? Check the logs:"
echo "  railway logs --tail 100"
echo ""
