# Hermes Autonomous Multi-Agent System

Komplexný autonomous AI systém s viacerými špecializovanými agentmi, ktorý proaktívne vyhľadáva informácie a kontaktuje používateľa cez Telegram.

## 🎯 Funkcie

- **7 Špecializovaných Agentov:**
  - 🔬 **AI Researcher** - AI/ML výskum, nové modely, breakthroughs
  - 💻 **Software Dev** - GitHub trending, dev tools, frameworks
  - 💰 **Crypto Agent** - Markets, DeFi, Polymarket predictions
  - ✅ **Productivity** - Task management, kalendár, daily reviews
  - 🐦 **Social Monitor** - Twitter/X, Reddit, HN monitoring
  - 🔍 **Web Researcher** - On-demand deep research
  - 🎯 **Orchestrator** - Koordinácia všetkých agentov

- **Proaktívne Vyhľadávanie:** 2-3 notifikácie denne s relevantným obsahom
- **Cross-Agent Collaboration:** Agenti komunikujú a zdieľajú objavy
- **Adaptive Learning:** Systém sa učí z užívateľského engagementu
- **Novelty Detection:** Dedupl ikácia a filtrovanie duplicitného obsahu
- **Budget Management:** Automatické riadenie API nákladov

## 📁 Štruktúra Projektu

```
hermes.ai/
├── autonomous/              # Core autonomous system
│   ├── __init__.py
│   ├── orchestrator.py     # Main coordinator
│   ├── goal_generator.py   # Proactive goal creation
│   ├── priority_queue.py   # Task scheduling
│   ├── agent_comms.py      # Inter-agent messaging (Redis)
│   ├── knowledge_base.py   # Shared PostgreSQL DB
│   └── novelty_detector.py # Deduplication & scoring
│
├── agents/                  # Agent profiles (7 agents)
│   ├── orchestrator/
│   │   ├── SOUL.md         # Personality
│   │   ├── config.yaml     # Configuration
│   │   ├── MEMORY.md       # Learned patterns
│   │   └── USER.md         # User preferences
│   ├── ai_researcher/
│   ├── software_dev/
│   ├── crypto_agent/
│   ├── productivity/
│   ├── social_monitor/
│   └── web_researcher/
│
├── skills/                  # Custom skills (5 new)
│   ├── ai-news-aggregator.md
│   ├── github-trending-analyzer.md
│   ├── crypto-market-digest.md
│   ├── productivity-daily-review.md
│   └── tech-news-synthesizer.md
│
├── cron_config.yaml        # Scheduling configuration
├── Dockerfile              # Docker image
├── docker-entrypoint.sh    # Startup script
├── requirements.txt        # Python dependencies
├── .env.example            # Environment variables template
└── README.md              # This file
```

## 🚀 Quick Start

### 1. Prerequisites

- [Railway CLI](https://docs.railway.app/develop/cli) nainštalované
- Telegram bot token (vytvor cez [@BotFather](https://t.me/BotFather))
- Anthropic/OpenAI API key

### 2. Telegram Bot Setup

```bash
# Na Telegrame, otvor @BotFather
/newbot
# Názov: Hermes Autonomous Agent
# Username: @your_hermes_bot (alebo iný dostupný)

# Dostaneš BOT_TOKEN - ulož si ho!

# Nastav príkazy:
/setcommands
start - Initialize conversation
help - Show commands
status - Check agent status
topics - Manage research topics
frequency - Adjust notification frequency
agents - List all agents
pause - Pause notifications
resume - Resume notifications
```

### 3. Railway Deployment

```bash
# Login do Railway
railway login

# Inicializuj projekt v hermes.ai/
cd /home/thinos/hermes.ai
railway init

# Vytvor projekt
# - Project name: "hermes-autonomous-agents"
# - Choose your workspace

# Link projekt
railway link

# Pridaj PostgreSQL
railway add --database postgres

# Pridaj Redis
railway add --database redis

# Nastav environment variables
railway variables set TELEGRAM_BOT_TOKEN="your_bot_token_here"
railway variables set ANTHROPIC_API_KEY="your_anthropic_key"

# Nastav webhook URL (nahraď s tvojím Railway URL)
railway variables set TELEGRAM_WEBHOOK_URL="https://hermes-autonomous-agents.up.railway.app"

# Optional: OpenAI (ak chceš použiť embeddings)
railway variables set OPENAI_API_KEY="your_openai_key"

# Optional: Browserbase (pre browser automation)
railway variables set BROWSERBASE_API_KEY="your_browserbase_key"
railway variables set BROWSERBASE_PROJECT_ID="your_project_id"

# Deploy!
railway up

# Monitor logs
railway logs --follow

# Otvor v browseri
railway open
```

### 4. Overenie Deployment

```bash
# Check status
railway status

# Check variables
railway variables list

# Check database connection
railway run python -c "from autonomous.knowledge_base import KnowledgeBase; kb = KnowledgeBase(); print(kb.get_stats()); kb.close()"

# Check Redis connection
railway run python -c "from autonomous.agent_comms import AgentCommunications; ac = AgentCommunications(); print(ac.get_stats()); ac.close()"
```

### 5. Test Telegram Bot

```bash
# Na Telegrame, otvor svojho bota
/start

# Mal by si dostať uvítaciu správu
# Ak nie, check logs:
railway logs --follow
```

## ⚙️ Konfigurácia

### Environment Variables

Všetky potrebné environment variables (Railway ich automaticky nastaví pri `railway add`):

| Variable | Popis | Required |
|----------|-------|----------|
| `DATABASE_URL` | PostgreSQL connection string | ✅ Yes |
| `REDIS_URL` | Redis connection string | ✅ Yes |
| `TELEGRAM_BOT_TOKEN` | Telegram bot token | ✅ Yes |
| `TELEGRAM_WEBHOOK_URL` | Public Railway URL | ✅ Yes |
| `ANTHROPIC_API_KEY` | Anthropic API key | ✅ Yes |
| `OPENAI_API_KEY` | OpenAI API key (optional) | ❌ No |
| `BROWSERBASE_API_KEY` | Browserbase API (optional) | ❌ No |
| `BROWSERBASE_PROJECT_ID` | Browserbase project (optional) | ❌ No |

### Cron Schedule Customization

Edit `cron_config.yaml` to adjust agent frequencies:

```yaml
ai_researcher:
  schedules:
    - name: "morning_scan"
      schedule: "0 9 * * *"  # Change to your preferred time
      # ...
```

### Agent Configuration

Každý agent má svoj `config.yaml` - môžeš upraviť:
- Model selection
- Temperature
- Max iterations
- Toolsets

Example:
```yaml
# agents/ai_researcher/config.yaml
model:
  provider: anthropic
  name: claude-3-5-sonnet-20241022
  temperature: 0.4
```

## 🎛️ Usage

### Telegram Commands

```
/start - Začni konverzáciu
/help - Zobraz help
/status - Status všetkých agentov
/topics - Manage research topics
/frequency - Zmena frekvencie notifikácií
/agents - List všetkých agentov
/pause - Pause notifikácie
/resume - Resume notifikácie
```

### Očakávané Notifikácie

**AI Researcher:** 3x denne (9:00, 15:00, 21:00)
- Nové AI papers, modely, breakthroughs

**Software Dev:** 2x denne (10:00, 18:00)
- GitHub trending, tech news, frameworks

**Crypto Agent:** 3x denne (8:00, 14:00, 20:00)
- Market snapshots, DeFi, Polymarket

**Productivity:** 2x denne (7:00, 19:00)
- Morning briefing, evening review

**Social Monitor:** 2x denne (11:00, 17:00)
- Twitter/Reddit/HN highlights

**Total:** ~2-3 aggregované digesty denne (nie všetky separátne!)

## 🔧 Development

### Local Testing

```bash
# Setup virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env with your credentials

# Run orchestrator locally
python -c "from autonomous.orchestrator import run_orchestrator_daemon; run_orchestrator_daemon()"
```

### Add New Skills

1. Vytvor nový skill súbor v `skills/`:
```markdown
---
name: my-new-skill
description: Description here
version: 1.0.0
---

# Skill content...
```

2. Pridaj skill do agent profile:
```bash
cp skills/my-new-skill.md agents/my_agent/skills/
```

3. Reference v `cron_config.yaml`:
```yaml
my_agent:
  schedules:
    - name: "my_task"
      skill: "my-new-skill"
```

### Add New Agent

1. Vytvor agent profile:
```bash
mkdir agents/new_agent
# Vytvor SOUL.md, config.yaml, MEMORY.md, USER.md
```

2. Pridaj do orchestrator:
```python
# autonomous/orchestrator.py
self.agents = [
    # ...
    "new_agent"
]
```

3. Pridaj goals do goal_generator:
```python
# autonomous/goal_generator.py
self.agent_goals["new_agent"] = {
    "topics": [...],
    "sources": [...],
    "frequency": "2x_daily"
}
```

## 📊 Monitoring

### Railway Dashboard

```bash
# Open Railway dashboard
railway open

# View logs
railway logs --follow

# Check metrics
railway status

# Database access
railway connect postgres
```

### Database Queries

```sql
-- Check recent discoveries
SELECT agent_name, topic, created_at, relevance_score
FROM agent_knowledge
ORDER BY created_at DESC
LIMIT 10;

-- Check task queue
SELECT agent_name, status, priority, goal
FROM task_queue
ORDER BY priority DESC
LIMIT 10;

-- Check user preferences
SELECT topic, engagement_score, notification_count
FROM user_preferences
ORDER BY engagement_score DESC;

-- Get agent performance
SELECT agent_name, COUNT(*) as discoveries, AVG(relevance_score) as avg_relevance
FROM agent_knowledge
WHERE created_at > NOW() - INTERVAL '7 days'
GROUP BY agent_name;
```

## 💰 Cost Estimation

**Monthly Costs:**
- **Railway Hobby:** $5/month (500 hours)
- **PostgreSQL:** Free tier OK (start), $5-10/month (scale)
- **Redis:** Free tier OK (start), $5/month (scale)
- **Anthropic API:** $30-60/month (depending on usage)
- **Optional APIs:** $10-30/month (Browserbase, OpenAI, etc.)

**Total:** ~$50-100/month

**Cost Optimization:**
- Adjust `cron_config.yaml` frequencies
- Set lower `daily_budget` in config
- Use cheaper models for simple tasks
- Enable caching and deduplication

## 🐛 Troubleshooting

### Bot Not Responding

```bash
# Check logs
railway logs --follow | grep "ERROR"

# Verify webhook
curl -X GET "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getWebhookInfo"

# Set webhook manually if needed
curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook?url=<YOUR_RAILWAY_URL>"
```

### Database Connection Issues

```bash
# Test connection
railway run python -c "from autonomous.knowledge_base import KnowledgeBase; kb = KnowledgeBase(); print('OK'); kb.close()"

# Check DATABASE_URL
railway variables get DATABASE_URL
```

### No Notifications

```bash
# Check cron schedules
railway run python -c "import yaml; print(yaml.safe_load(open('cron_config.yaml')))"

# Check orchestrator logs
railway logs --follow | grep "orchestrator"

# Manually trigger scan
railway run python -c "
from autonomous.orchestrator import Orchestrator
orch = Orchestrator()
orch.trigger_agent_scan('ai_researcher')
orch.coordinate()
"
```

## 📚 Architecture

```
┌─────────────────────────────────────┐
│         ORCHESTRATOR                │
│   (Coordination & Prioritization)   │
└─────────┬───────────────────────────┘
          │
    ┌─────┴─────┐
    │           │
    │   Shared  │
    │   Memory  │
    │           │
    ├───────────┤
    │ PostgreSQL│ (Knowledge Base)
    │   Redis   │ (Pub/Sub)
    └───────────┘
          │
┌─────────┴────────────────────────────┐
│                                      │
▼                                      ▼
[AI Researcher]  [Software Dev]
[Crypto Agent]   [Productivity]
[Social Monitor] [Web Researcher]
│
└──────────► Telegram Bot ──────► User
```

## 🤝 Contributing

This is a personal project, but ideas welcome! Open an issue or PR.

## 📄 License

MIT License - see [Hermes Agent License](https://github.com/NousResearch/hermes-agent)

## 🙏 Credits

- Built on top of [Hermes Agent](https://github.com/NousResearch/hermes-agent) by Nous Research
- Inspired by autonomous agent research
- Powered by Anthropic Claude

---

**Vyrobil:** thinos
**Verzia:** 1.0.0
**Dátum:** 2026-07-06
