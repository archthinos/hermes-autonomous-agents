# ⚡ Quick Start Guide

Najrýchlejšia cesta k spusteniu Hermes Autonomous Agent System.

## 🚀 5-Minute Deployment

### 1. Telegram Bot (2 min)

```
1. Otvor Telegram
2. Vyhľadaj: @BotFather
3. Pošli: /newbot
4. Názov: Hermes Autonomous Agent
5. Username: @tvoj_hermes_bot
6. Ulož BOT_TOKEN
```

### 2. Railway Setup (3 min)

```bash
# Install Railway CLI (if not installed)
npm install -g @railway/cli
# or
brew install railway

# Login
railway login

# Init project
cd /home/thinos/hermes.ai
railway init
# → Create new project
# → Name: hermes-autonomous-agents

# Add databases
railway add
# → Select: PostgreSQL

railway add
# → Select: Redis

# Set credentials
railway variables set TELEGRAM_BOT_TOKEN="tvoj_token_z_botfather"
railway variables set ANTHROPIC_API_KEY="sk-ant-..."

# Deploy!
railway up

# Get URL
railway open
# Copy URL (napr: https://hermes-autonomous-agents.up.railway.app)

# Set webhook
railway variables set TELEGRAM_WEBHOOK_URL="https://tvoj-url.up.railway.app"

# Redeploy
railway up
```

### 3. Test (30 sec)

```
1. Otvor Telegram
2. Nájdi svojho bota
3. Pošli: /start
4. Dostaneš welcome message!
```

## ✅ Checklist

- [ ] Telegram bot vytvorený (@BotFather)
- [ ] Railway CLI nainštalované
- [ ] Railway projekt vytvorený
- [ ] PostgreSQL pridané
- [ ] Redis pridané
- [ ] TELEGRAM_BOT_TOKEN nastavený
- [ ] ANTHROPIC_API_KEY nastavený
- [ ] Deployed (railway up)
- [ ] TELEGRAM_WEBHOOK_URL nastavený
- [ ] Redeployed
- [ ] Bot odpovedá na /start

## 🎯 Po Deploymene

### Verify System

```bash
# Check logs
railway logs --follow

# Should see:
✓ PostgreSQL is ready!
✓ Redis is ready!
✓ Database schema initialized
✓ Starting Telegram bot...
✓ Starting cron scheduler...
```

### Test Commands

V Telegrame:
- `/start` - Welcome message
- `/status` - System status
- `/help` - Help

### Monitor

```bash
# Live logs
railway logs --follow

# Check status
railway status

# Database
railway connect postgres
```

## 🎨 Customize

### Adjust Schedules

Edit `cron_config.yaml`:
```yaml
ai_researcher:
  schedules:
    - schedule: "0 9 * * *"  # Change time here
```

Then:
```bash
railway up  # Redeploy
```

### Change Notification Frequency

```bash
railway variables set MAX_NOTIFICATIONS_PER_DAY="5"
railway restart
```

### Adjust Budget

```bash
railway variables set DAILY_BUDGET="30.0"
railway restart
```

## 📊 Expected Behavior

### First 24 Hours

- **9:00** - AI Research morning scan
- **10:00** - Software Dev GitHub scan
- **11:00** - Social Monitor Twitter/Reddit
- **14:00** - Crypto market midday
- **15:00** - AI Research afternoon check
- **17:00** - Social Monitor HN scan
- **18:00** - Software Dev evening news
- **19:00** - Productivity evening review
- **21:00** - AI Research evening digest

### Aggregated Digests

Systém kombinuje objavy a posiela **2-3 digesty denne**, nie každý samostatne!

## 🐛 Troubleshooting

### Bot nie je online

```bash
railway logs | grep ERROR
railway status
railway restart
```

### Database error

```bash
railway connect postgres
# Check if accessible
railway logs | grep "database"
```

### Žiadne notifikácie

```bash
# Check cron logs
railway logs | grep "CRON"

# Manually trigger
railway run python -c "
from autonomous.orchestrator import Orchestrator
o = Orchestrator()
o.trigger_agent_scan('ai_researcher')
"
```

## 💰 Costs

- Railway: $5/month (Hobby)
- PostgreSQL: $0-10/month
- Redis: $0-5/month
- Anthropic API: $30-60/month

**Total: ~$50-80/month**

## 📚 More Info

- Full README: [README.md](README.md)
- Deployment Guide: [DEPLOYMENT.md](DEPLOYMENT.md)
- Test System: `python3 test_system.py`

---

**Need Help?** Open an issue or check Railway logs!
