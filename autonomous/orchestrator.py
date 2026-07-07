"""
Orchestrator - Main Coordinator for Multi-Agent System

The orchestrator is the brain of the autonomous system. It:
- Coordinates all specialized agents
- Manages the priority queue
- Generates proactive goals
- Handles inter-agent communication
- Tracks budget and resources
- Learns from user engagement
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import time

from .knowledge_base import KnowledgeBase
from .agent_comms import AgentCommunications
from .priority_queue import PriorityQueue, Task, TaskType, TaskStatus
from .goal_generator import GoalGenerator
from .novelty_detector import NoveltyDetector

logger = logging.getLogger(__name__)


class Orchestrator:
    """
    Master coordinator for the autonomous multi-agent system.

    Responsibilities:
    1. Generate proactive research goals for agents
    2. Manage task priority queue
    3. Monitor agent activity and load balancing
    4. Filter and aggregate agent discoveries
    5. Coordinate cross-agent collaboration
    6. Track budget and resource usage
    7. Learn from user engagement
    """

    def __init__(
        self,
        database_url: Optional[str] = None,
        redis_url: Optional[str] = None,
        daily_budget: float = 50.0,
        notification_target_count: int = 3  # 2-3 per day
    ):
        """
        Initialize orchestrator.

        Args:
            database_url: PostgreSQL connection string
            redis_url: Redis connection string
            daily_budget: Daily API budget (USD)
            notification_target_count: Target notifications per day
        """
        # Initialize core components
        self.kb = KnowledgeBase(database_url)
        self.comms = AgentCommunications(redis_url)
        self.queue = PriorityQueue(self.kb, daily_budget=daily_budget)
        self.goal_gen = GoalGenerator(self.kb)
        self.novelty = NoveltyDetector(self.kb)

        self.notification_target = notification_target_count
        self.notifications_sent_today = 0
        self.notification_reset_at = datetime.now().replace(hour=0, minute=0) + timedelta(days=1)

        # Agent registry
        self.agents = [
            "ai_researcher",
            "software_dev",
            "crypto_agent",
            "productivity",
            "social_monitor",
            "web_researcher"  # On-demand only
        ]

        # Start listening for agent communications
        self._setup_communication_handlers()

        logger.info("Orchestrator initialized")

    # ==================== Main Coordination Loop ====================

    def coordinate(self):
        """
        Main coordination cycle.

        This should be called periodically (e.g., every 4 hours) by the cron scheduler.
        """
        logger.info("=" * 60)
        logger.info("ORCHESTRATOR COORDINATION CYCLE STARTED")
        logger.info("=" * 60)

        # 1. Check and reset daily counters
        self._check_daily_reset()

        # 2. Get system status
        status = self.get_system_status()
        logger.info(f"System Status: {status}")

        # 3. Generate new goals for agents
        self._generate_agent_goals()

        # 4. Process pending tasks
        self._process_task_queue()

        # 5. Review and aggregate recent discoveries
        self._review_discoveries()

        # 6. Check if we should send user notification
        self._check_notification_threshold()

        # 7. Cleanup old data
        self._periodic_cleanup()

        logger.info("ORCHESTRATOR COORDINATION CYCLE COMPLETED")
        logger.info("=" * 60)

    # ==================== Goal Generation ====================

    def _generate_agent_goals(self):
        """Generate proactive goals for all agents."""
        logger.info("Generating proactive goals for agents...")

        context = {
            "time": datetime.now().hour,
            "day_of_week": datetime.now().weekday(),
            "budget_remaining": self.queue.get_budget_status()["remaining"]
        }

        for agent_name in self.agents:
            # Skip web_researcher (on-demand only)
            if agent_name == "web_researcher":
                continue

            try:
                goals = self.goal_gen.generate_goals_for_agent(agent_name, context)

                for goal_data in goals:
                    # Create task in queue
                    self.queue.add_task(
                        agent_name=agent_name,
                        task_type=TaskType.RESEARCH,
                        goal=goal_data["goal"],
                        urgency=goal_data.get("priority", 50),
                        importance=goal_data.get("priority", 50),
                        metadata=goal_data.get("metadata", {})
                    )

                logger.info(f"  {agent_name}: {len(goals)} goals generated")

            except Exception as e:
                logger.error(f"Failed to generate goals for {agent_name}: {e}")

    # ==================== Task Queue Processing ====================

    def _process_task_queue(self):
        """Process pending tasks from priority queue."""
        logger.info("Processing task queue...")

        budget_status = self.queue.get_budget_status()
        logger.info(f"Budget: ${budget_status['used_today']:.2f} / ${budget_status['daily_budget']:.2f} used")

        # Process tasks until queue empty or budget exhausted
        processed = 0
        max_tasks_per_cycle = 10  # Limit per coordination cycle

        while processed < max_tasks_per_cycle:
            task = self.queue.get_next_task(respect_budget=True)

            if not task:
                logger.info("No more tasks available or budget exhausted")
                break

            logger.info(f"Processing task {task.id}: {task.goal[:60]}...")

            # Execute task
            success = self._execute_task(task)

            processed += 1

        logger.info(f"Processed {processed} tasks")

    def _execute_task(self, task: Task) -> bool:
        """
        Execute a task.

        Args:
            task: Task to execute

        Returns:
            True if successful
        """
        # Start task
        self.queue.start_task(task.id)

        try:
            # TODO: Actually execute the task by calling the agent
            # For now, simulate execution
            logger.info(f"  Executing: {task.agent_name} - {task.goal[:50]}...")

            # Simulate research results
            result = {
                "findings": [
                    f"Discovery 1 for {task.goal[:30]}",
                    f"Discovery 2 for {task.goal[:30]}"
                ],
                "sources": ["source1.com", "source2.com"],
                "confidence": 0.8
            }

            result_str = str(result)

            # Mark as completed
            self.queue.complete_task(
                task_id=task.id,
                result=result_str,
                actual_cost=task.estimated_cost,
                success=True
            )

            # Store discoveries in knowledge base
            for finding in result["findings"]:
                novelty_score = self.novelty.calculate_novelty_score(
                    content=finding,
                    topic=task.metadata.get("topic", "general")
                )

                if novelty_score > 0.5:  # Only store novel findings
                    self.kb.store_knowledge(
                        agent_name=task.agent_name,
                        topic=task.metadata.get("topic", "general"),
                        content=finding,
                        relevance_score=novelty_score,
                        metadata={"task_id": task.id, "source": task.metadata.get("source")}
                    )

            return True

        except Exception as e:
            logger.error(f"Task {task.id} failed: {e}")

            # Mark as failed and potentially retry
            self.queue.complete_task(
                task_id=task.id,
                result=f"Failed: {str(e)}",
                actual_cost=0.0,
                success=False
            )

            if task.can_retry:
                self.queue.retry_task(task.id)

            return False

    # ==================== Discovery Review ====================

    def _review_discoveries(self):
        """Review recent discoveries and prepare for notification."""
        logger.info("Reviewing recent discoveries...")

        # Get discoveries from last coordination cycle (4 hours)
        recent = self.kb.search_knowledge(limit=50)

        if not recent:
            logger.info("No recent discoveries")
            return

        # Filter for high-quality, novel content
        high_quality = [
            d for d in recent
            if d.get("relevance_score", 0) > 0.6 and d.get("user_engagement", 0) >= 0
        ]

        logger.info(f"Found {len(high_quality)} high-quality discoveries")

        # Group by topic for potential aggregation
        by_topic = {}
        for discovery in high_quality:
            topic = discovery.get("topic", "general")
            if topic not in by_topic:
                by_topic[topic] = []
            by_topic[topic].append(discovery)

        # Check if we have enough for a notification
        if len(high_quality) >= 3:  # At least 3 quality items
            logger.info("Sufficient discoveries for notification")
            # Notification would be sent by the agent that discovered them
            # Orchestrator just tracks the count
        else:
            logger.info("Insufficient discoveries for notification yet")

    # ==================== Agent Communication ====================

    def _setup_communication_handlers(self):
        """Setup handlers for agent communication channels."""

        def handle_discovery(message: Dict):
            """Handle discovery from agents."""
            logger.info(f"Discovery from {message['agent']}: {message['topic']}")

            # Store in knowledge base
            self.kb.store_knowledge(
                agent_name=message["agent"],
                topic=message["topic"],
                content=message["content"],
                relevance_score=message.get("relevance", 0.5),
                metadata=message.get("metadata", {})
            )

        def handle_question(message: Dict):
            """Handle questions from agents."""
            logger.info(f"Question from {message['agent']}: {message['question']}")

            # If addressed to orchestrator, create research task
            if message.get("target") == "orchestrator":
                self.queue.add_task(
                    agent_name="web_researcher",
                    task_type=TaskType.RESEARCH,
                    goal=message["question"],
                    urgency=80 if message.get("urgency") == "high" else 60,
                    importance=70,
                    metadata={"requester": message["agent"]}
                )

        def handle_alert(message: Dict):
            """Handle alerts from agents."""
            severity = message.get("severity", "info")
            logger.log(
                logging.ERROR if severity == "error" else logging.WARNING,
                f"Alert from {message['agent']}: {message['message']}"
            )

        # Subscribe to channels
        self.comms.subscribe_discoveries(handle_discovery)
        self.comms.subscribe_questions(handle_question, agent_name="orchestrator")
        self.comms.subscribe_alerts(handle_alert, min_severity="warning")

        # Start listening
        self.comms.start_listening()

    # ==================== Notification Management ====================

    def _check_notification_threshold(self):
        """Check if we should send notification to user."""
        if self.notifications_sent_today >= self.notification_target:
            logger.info(f"Notification target reached ({self.notification_target}/day)")
            return

        # Get high-priority discoveries
        high_priority = self.kb.search_knowledge(min_relevance=0.7, limit=10)

        if len(high_priority) >= 3:
            logger.info(f"Ready to send notification ({len(high_priority)} items)")
            # TODO: Trigger notification via Telegram
            self.notifications_sent_today += 1
        else:
            logger.info(f"Not enough high-priority items for notification ({len(high_priority)}/3)")

    def _check_daily_reset(self):
        """Reset daily counters if new day."""
        if datetime.now() >= self.notification_reset_at:
            logger.info(f"Daily reset: {self.notifications_sent_today} notifications sent yesterday")
            self.notifications_sent_today = 0
            self.notification_reset_at = datetime.now().replace(hour=0, minute=0) + timedelta(days=1)

    # ==================== Cleanup & Maintenance ====================

    def _periodic_cleanup(self):
        """Periodic cleanup of old data."""
        try:
            self.kb.cleanup_expired()
            self.queue.cleanup_old_tasks(days=30)
            logger.info("Cleanup completed")
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")

    # ==================== Status & Monitoring ====================

    def get_system_status(self) -> Dict:
        """Get comprehensive system status."""
        kb_stats = self.kb.get_stats()
        queue_stats = self.queue.get_stats()
        budget = self.queue.get_budget_status()
        comms_stats = self.comms.get_stats()

        return {
            "timestamp": datetime.now().isoformat(),
            "knowledge_base": kb_stats,
            "task_queue": queue_stats,
            "budget": budget,
            "communications": comms_stats,
            "notifications_today": self.notifications_sent_today,
            "notification_target": self.notification_target,
            "agents": {
                agent: {
                    "load": self.queue.get_agent_load(agent),
                    "status": self.comms.get_agent_status(agent)
                }
                for agent in self.agents
            }
        }

    def get_agent_performance(self, agent_name: str, days: int = 7) -> Dict:
        """Get performance metrics for an agent."""
        # Get recent knowledge from this agent
        discoveries = self.kb.search_knowledge(agent_name=agent_name, limit=100)

        # Calculate metrics
        total_discoveries = len(discoveries)
        avg_relevance = sum(d.get("relevance_score", 0) for d in discoveries) / max(total_discoveries, 1)
        avg_engagement = sum(d.get("user_engagement", 0) for d in discoveries) / max(total_discoveries, 1)

        return {
            "agent": agent_name,
            "period_days": days,
            "total_discoveries": total_discoveries,
            "avg_relevance_score": avg_relevance,
            "avg_user_engagement": avg_engagement,
            "discoveries_per_day": total_discoveries / days
        }

    # ==================== Manual Controls ====================

    def trigger_agent_scan(self, agent_name: str, goal: Optional[str] = None):
        """Manually trigger an agent scan."""
        if agent_name not in self.agents:
            logger.error(f"Unknown agent: {agent_name}")
            return

        if not goal:
            # Generate default goal for agent
            goals = self.goal_gen.generate_goals_for_agent(agent_name)
            if not goals:
                logger.warning(f"No goals generated for {agent_name}")
                return
            goal = goals[0]["goal"]

        # Create high-priority task
        self.queue.add_task(
            agent_name=agent_name,
            task_type=TaskType.RESEARCH,
            goal=goal,
            urgency=90,
            importance=90
        )

        logger.info(f"Manual scan triggered for {agent_name}: {goal}")

    def adjust_agent_frequency(self, agent_name: str, frequency: str):
        """Adjust agent's scanning frequency."""
        # TODO: Implement frequency adjustment
        logger.info(f"Frequency adjustment for {agent_name}: {frequency}")

    def pause_agent(self, agent_name: str):
        """Pause an agent's activity."""
        # TODO: Implement agent pausing
        logger.info(f"Agent {agent_name} paused")

    def resume_agent(self, agent_name: str):
        """Resume an agent's activity."""
        # TODO: Implement agent resuming
        logger.info(f"Agent {agent_name} resumed")

    # ==================== Shutdown ====================

    def shutdown(self):
        """Gracefully shutdown orchestrator."""
        logger.info("Orchestrator shutting down...")

        # Stop communications
        self.comms.stop_listening()
        self.comms.close()

        # Close database
        self.kb.close()

        logger.info("Orchestrator shutdown complete")


# ==================== Standalone Execution ====================

def run_orchestrator_daemon(interval_hours: int = 4):
    """
    Run orchestrator as a daemon process.

    Args:
        interval_hours: Hours between coordination cycles
    """
    orchestrator = Orchestrator()

    logger.info(f"Starting orchestrator daemon (interval: {interval_hours}h)")

    try:
        while True:
            orchestrator.coordinate()

            # Sleep until next cycle
            sleep_seconds = interval_hours * 3600
            logger.info(f"Sleeping for {interval_hours} hours...")
            time.sleep(sleep_seconds)

    except KeyboardInterrupt:
        logger.info("Daemon interrupted by user")
    except Exception as e:
        logger.error(f"Daemon error: {e}")
    finally:
        orchestrator.shutdown()


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Run daemon
    run_orchestrator_daemon(interval_hours=4)
