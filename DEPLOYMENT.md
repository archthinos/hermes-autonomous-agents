# 🚀 Railway Deployment Guide

Quick step-by-step guide for deploying Hermes Autonomous Agent System to Railway.

## Prerequisites

- Railway CLI installed: `npm install -g @railway/cli` alebo `brew install railway`
- Telegram bot token (from @BotFather)
- Anthropic API key (from console.anthropic.com)

## Step 1: Railway Login

```bash
railway login
```

Browser sa otvorí pre login. Po prihlásení sa vráť do terminálu.

## Step 2: Initialize Project

```bash
cd /home/thinos/hermes.ai
railway init
```

**Output:**
```
✔ Select a project · Create new project
✔ Enter project name · hermes-autonomous-agents
✔ Environment · production
```

## Step 3: Add Databases

```bash
# Add PostgreSQL
railway add

# Select: PostgreSQL
# Railway automatically creates DATABASE_URL variable

# Add Redis
railway add

# Select: Redis
# Railway automatically creates REDIS_URL variable
```

## Step 4: Set Environment Variables

```bash
# Required: Telegram Bot Token
railway variables set TELEGRAM_BOT_TOKEN="YOUR_BOT_TOKEN_HERE"

# Required: LLM API Key
railway variables set ANTHROPIC_API_KEY="YOUR_ANTHROPIC_KEY_HERE"

# Required: Webhook URL (replace with your Railway URL after first deploy)
# You'll get this URL after first deploy, then update it
railway variables set TELEGRAM_WEBHOOK_URL="https://your-app.up.railway.app"

# Optional but recommended
railway variables set OPENAI_API_KEY="YOUR_OPENAI_KEY"
railway variables set BROWSERBASE_API_KEY="YOUR_BROWSERBASE_KEY"
railway variables set BROWSERBASE_PROJECT_ID="YOUR_PROJECT_ID"

# Configuration
railway variables set DAILY_BUDGET="50.0"
railway variables set MAX_NOTIFICATIONS_PER_DAY="3"
railway variables set LOG_LEVEL="INFO"
```

## Step 5: First Deploy

```bash
railway up
```

Railway will:
1. Build Docker image
2. Push to Railway
3. Start your application
4. Assign a public URL

**Wait for:**
```
✔ Build completed
✔ Deployment successful
```

## Step 6: Get Your Railway URL

```bash
railway open
```

This opens your Railway dashboard. Copy the public URL (looks like: `https://hermes-autonomous-agents.up.railway.app`)

## Step 7: Update Webhook URL

```bash
# Update with your actual Railway URL
railway variables set TELEGRAM_WEBHOOK_URL="https://hermes-autonomous-agents.up.railway.app"

# Redeploy
railway up
```

## Step 8: Verify Deployment

```bash
# Check logs
railway logs

# Should see:
# ✓ PostgreSQL is ready!
# ✓ Redis is ready!
# ✓ Database schema initialized
# ✓ Starting Telegram bot...
# ✓ Starting cron scheduler...
```

## Step 9: Test Telegram Bot

1. Open Telegram
2. Search for your bot (@your_bot_name)
3. Send `/start`
4. You should get welcome message!

## Step 10: Verify Cron Scheduler

```bash
railway logs --follow
```

Watch for scheduled tasks executing:
```
CRON: Running orchestrator coordination cycle
CRON: Executing ai_researcher task
Task 123 created (priority: 70)
```

## Troubleshooting

### Bot Not Responding

```bash
# Check if webhook is set correctly
curl "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getWebhookInfo"

# Manual webhook set
curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook?url=https://your-app.up.railway.app/<YOUR_BOT_TOKEN>"
```

### Database Connection Failed

```bash
# Test DATABASE_URL
railway run python -c "import psycopg2; psycopg2.connect('$DATABASE_URL'); print('OK')"
```

### Application Crashed

```bash
# Check logs
railway logs --tail 100

# Common issues:
# 1. Missing environment variables
# 2. Database not ready (wait 30s after deploy)
# 3. Port conflict (Railway sets PORT automatically)
```

## Monitoring Commands

```bash
# View logs (live)
railway logs --follow

# View logs (last 100 lines)
railway logs --tail 100

# Check status
railway status

# Check variables
railway variables

# Check services
railway service

# Open dashboard
railway open
```

## Useful Railway Commands

```bash
# Deploy new version
railway up

# Restart application
railway restart

# Connect to PostgreSQL
railway connect postgres

# Connect to Redis
railway connect redis

# Run command in Railway environment
railway run python main.py

# Shell access
railway shell
```

## Cost Monitoring

Railway Hobby Plan: $5/month includes:
- 500 execution hours
- $5 usage credits

Additional costs:
- PostgreSQL: ~$5-10/month (after free tier)
- Redis: ~$5/month (after free tier)

**Total: ~$15-20/month infrastructure**

Plus API costs (Anthropic, etc): ~$30-60/month

**Grand Total: ~$45-80/month**

## Scaling

If you need more power:

```bash
# Railway Pro Plan ($20/month):
# - More execution hours
# - Higher resource limits
# - Priority support
```

## Backup & Recovery

```bash
# Backup PostgreSQL
railway connect postgres
# Then: pg_dump ...

# Export environment variables
railway variables > variables_backup.txt

# Export logs
railway logs --tail 10000 > logs_backup.txt
```

## Updates

When you make code changes:

```bash
git add .
git commit -m "Update: description"
railway up
```

Railway will rebuild and redeploy automatically.

---

**Need help?** Check Railway docs: https://docs.railway.app
