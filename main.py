#!/usr/bin/env python3
"""
Hermes Autonomous Multi-Agent System - Main Entry Point

This is the main application that runs:
1. Telegram Bot Gateway (for user interaction)
2. Cron Scheduler (for proactive agent tasks)
3. Orchestrator (for coordination)

Designed for Railway deployment with webhook mode.
"""

import os
import sys
import logging
import signal
import time
from threading import Thread

# Setup logging
logging.basicConfig(
    level=os.getenv('LOG_LEVEL', 'INFO'),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def check_environment():
    """Check that all required environment variables are set."""
    required_vars = [
        'DATABASE_URL',
        'REDIS_URL',
        'TELEGRAM_BOT_TOKEN'
    ]

    missing = []
    for var in required_vars:
        if not os.getenv(var):
            missing.append(var)

    if missing:
        logger.error(f"Missing required environment variables: {', '.join(missing)}")
        logger.error("Please set these variables before starting the application.")
        return False

    # Check optional but recommended
    optional_vars = ['ANTHROPIC_API_KEY', 'OPENAI_API_KEY', 'TELEGRAM_WEBHOOK_URL']
    for var in optional_vars:
        if not os.getenv(var):
            logger.warning(f"Optional variable not set: {var}")

    return True


def run_telegram_gateway():
    """
    Run Telegram gateway (webhook or polling mode).

    This would normally use the Hermes gateway system, but for this
    autonomous system, we're implementing a simple bot.
    """
    from telegram import Update
    from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

    logger.info("Starting Telegram bot...")

    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    webhook_url = os.getenv('TELEGRAM_WEBHOOK_URL')
    port = int(os.getenv('PORT', 8080))

    # Create application
    application = Application.builder().token(bot_token).build()

    # Command handlers
    async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command."""
        welcome_message = """
🤖 **Hermes Autonomous Agent System**

Vitaj! Som tvoj autonomný AI asistent s 7 špecializovanými agentmi:

🔬 **AI Researcher** - AI/ML výskum a novinky
💻 **Software Dev** - GitHub trending, dev tools
💰 **Crypto Agent** - Crypto markets, DeFi
✅ **Productivity** - Task management, denné review
🐦 **Social Monitor** - Twitter, Reddit, HN
🔍 **Web Researcher** - Deep research na požiadanie
🎯 **Orchestrator** - Koordinácia všetkých agentov

**Proaktívne správanie:**
- Vyhľadávam informácie 2-3x denne automaticky
- Posielam ti len relevantný, nový obsah
- Učím sa z tvojich reakcií
- Koordinujem medzi agentmi

**Príkazy:**
/status - Status systému
/topics - Manage research topics
/pause - Pause notifikácie
/resume - Resume notifikácie
/help - Pomoc

Systém je aktívny a začína vyhľadávať! 🚀
"""
        await update.message.reply_text(welcome_message, parse_mode='Markdown')

    async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command."""
        from autonomous.orchestrator import Orchestrator

        try:
            orch = Orchestrator()
            status = orch.get_system_status()

            message = f"""
📊 **System Status**

**Task Queue:**
- Pending: {status['task_queue']['pending']}
- Running: {status['task_queue']['running']}
- Completed: {status['task_queue']['completed']}

**Budget:**
- Used: ${status['budget']['used_today']:.2f}
- Remaining: ${status['budget']['remaining']:.2f}

**Knowledge Base:**
- Total entries: {status['knowledge_base'].get('agent_knowledge', 0)}

**Notifications Today:** {status['notifications_today']}/{status['notification_target']}

**Agents Active:** {status['communications']['active_agents']}

Všetko beží smooth! ✅
"""
            await update.message.reply_text(message, parse_mode='Markdown')
            orch.shutdown()

        except Exception as e:
            logger.error(f"Status command error: {e}")
            await update.message.reply_text(f"Error getting status: {str(e)}")

    async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command."""
        help_text = """
📚 **Hermes Agent - Pomoc**

**Príkazy:**
/start - Začať konverzáciu
/status - System status
/topics - Manage research topics (coming soon)
/pause - Pause autonomous notifications
/resume - Resume notifications
/help - Táto pomoc

**Ako to funguje:**
1. Agenti automaticky vyhľadávajú info podľa schedulu
2. Systém filtruje duplicity a low-quality content
3. Dostaneš 2-3 digesty denne s top objavmi
4. Systém sa učí z tvojich reakcií (👍/👎)

**Môžeš aj proaktívne pýtať:**
"Nájdi mi info o XYZ" - Web Researcher urobí deep dive
"Čo je nové v AI?" - AI Researcher ti povie aktuálny stav
"Aké su crypto ceny?" - Crypto Agent ti dá market snapshot

Poznámka: Agenti sú aktívni len počas nakonfigurovaných časov (pozri cron_config.yaml)
"""
        await update.message.reply_text(help_text, parse_mode='Markdown')

    async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle regular messages."""
        # TODO: Integrate with Hermes agent for conversation
        message = update.message.text

        # For now, simple acknowledgment
        await update.message.reply_text(
            "Prijal som tvoju správu. Konverzačný mód zatiaľ nie je plne implementovaný, "
            "ale autonomous agenti sú aktívni a budú ťa kontaktovať s objavmi! 🔍"
        )

    # Register handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Run bot
    if webhook_url:
        # Webhook mode (for Railway)
        # Extract base URL without /webhook suffix for proper setup
        base_url = webhook_url.replace("/webhook", "")
        webhook_path = f"/webhook/{bot_token}"
        full_webhook_url = f"{base_url}{webhook_path}"

        logger.info(f"Running in webhook mode: {full_webhook_url}")
        application.run_webhook(
            listen="0.0.0.0",
            port=port,
            url_path=webhook_path,
            webhook_url=full_webhook_url
        )
    else:
        # Polling mode (for local development)
        logger.info("Running in polling mode")
        application.run_polling()


def run_cron_scheduler():
    """Run the cron scheduler in background."""
    from autonomous.cron_scheduler import run_scheduler_daemon

    logger.info("Starting cron scheduler...")

    try:
        run_scheduler_daemon(config_path="cron_config.yaml")
    except Exception as e:
        logger.error(f"Cron scheduler error: {e}", exc_info=True)


def main():
    """Main application entry point."""
    logger.info("=" * 60)
    logger.info("HERMES AUTONOMOUS MULTI-AGENT SYSTEM")
    logger.info("=" * 60)

    # Check environment
    if not check_environment():
        logger.error("Environment check failed. Exiting.")
        sys.exit(1)

    logger.info("Environment check passed ✓")

    # Determine run mode
    run_mode = os.getenv('RUN_MODE', 'full')  # full, scheduler_only, bot_only

    if run_mode == 'scheduler_only':
        logger.info("Running in SCHEDULER ONLY mode")
        run_cron_scheduler()

    elif run_mode == 'bot_only':
        logger.info("Running in BOT ONLY mode")
        run_telegram_gateway()

    else:  # full mode
        logger.info("Running in FULL mode (bot + scheduler)")

        # Start scheduler in background thread
        scheduler_thread = Thread(target=run_cron_scheduler, daemon=True)
        scheduler_thread.start()

        # Wait a bit for scheduler to initialize
        time.sleep(2)

        # Run Telegram bot in main thread
        try:
            run_telegram_gateway()
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        except Exception as e:
            logger.error(f"Application error: {e}", exc_info=True)
        finally:
            logger.info("Shutting down...")


if __name__ == "__main__":
    main()
