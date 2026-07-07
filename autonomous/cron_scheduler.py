"""
Cron Scheduler - Scheduled Task Execution for Autonomous Agents

Reads cron_config.yaml and executes agent tasks on schedule.
Integrates with Orchestrator for coordination.
"""

import logging
import yaml
import os
from typing import Dict, List, Optional
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
import pytz

from .orchestrator import Orchestrator
from .priority_queue import TaskType

logger = logging.getLogger(__name__)


class CronScheduler:
    """
    Manages scheduled execution of agent tasks based on cron_config.yaml.

    Features:
    - Load cron schedules from YAML config
    - Schedule jobs using APScheduler
    - Integrate with Orchestrator
    - Track job execution and errors
    - Support timezone-aware scheduling
    """

    def __init__(
        self,
        config_path: str = "cron_config.yaml",
        orchestrator: Optional[Orchestrator] = None,
        timezone: str = "Europe/Bratislava"
    ):
        """
        Initialize cron scheduler.

        Args:
            config_path: Path to cron_config.yaml
            orchestrator: Orchestrator instance (creates new if None)
            timezone: Timezone for scheduling
        """
        self.config_path = config_path
        self.orchestrator = orchestrator or Orchestrator()
        self.timezone = pytz.timezone(timezone)

        # Load configuration
        self.config = self._load_config()

        # Initialize APScheduler
        self.scheduler = BackgroundScheduler(timezone=self.timezone)
        self.scheduler.add_listener(self._job_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)

        # Job registry
        self.jobs = {}

        logger.info(f"CronScheduler initialized (timezone: {timezone})")

    def _load_config(self) -> Dict:
        """Load cron configuration from YAML file."""
        if not os.path.exists(self.config_path):
            logger.error(f"Config file not found: {self.config_path}")
            raise FileNotFoundError(f"Config file not found: {self.config_path}")

        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            logger.info(f"Loaded cron config from {self.config_path}")
            return config
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            raise

    # ==================== Job Scheduling ====================

    def schedule_all(self):
        """Schedule all jobs from configuration."""
        logger.info("Scheduling all agent jobs...")

        # Schedule orchestrator first
        self._schedule_orchestrator()

        # Schedule each agent
        for agent_name, agent_config in self.config.items():
            if agent_name in ['global', 'timezone', 'logging']:
                continue  # Skip global config

            if not agent_config.get('enabled', True):
                logger.info(f"Agent {agent_name} disabled, skipping")
                continue

            # Handle single schedule vs. multiple schedules
            schedules = agent_config.get('schedules', [])
            if not schedules and agent_config.get('schedule'):
                # Single schedule format
                self._schedule_agent_job(
                    agent_name=agent_name,
                    schedule=agent_config['schedule'],
                    goal=agent_config.get('goal', ''),
                    config=agent_config
                )
            else:
                # Multiple schedules format
                for schedule_config in schedules:
                    self._schedule_agent_job(
                        agent_name=agent_name,
                        schedule=schedule_config['schedule'],
                        goal=schedule_config.get('goal', ''),
                        config=schedule_config,
                        job_name=schedule_config.get('name', 'default')
                    )

        logger.info(f"Scheduled {len(self.jobs)} jobs total")

    def _schedule_orchestrator(self):
        """Schedule the orchestrator coordination cycle."""
        orch_config = self.config.get('orchestrator', {})

        if not orch_config.get('enabled', True):
            logger.warning("Orchestrator disabled - this may cause issues!")
            return

        schedule = orch_config.get('schedule', '0 */4 * * *')  # Default: every 4h

        job_id = 'orchestrator_coordination'
        job = self.scheduler.add_job(
            func=self._run_orchestrator_cycle,
            trigger=CronTrigger.from_crontab(schedule, timezone=self.timezone),
            id=job_id,
            name='Orchestrator Coordination Cycle',
            replace_existing=True
        )

        self.jobs[job_id] = {
            'job': job,
            'type': 'orchestrator',
            'schedule': schedule
        }

        logger.info(f"Scheduled orchestrator: {schedule}")

    def _schedule_agent_job(
        self,
        agent_name: str,
        schedule: str,
        goal: str,
        config: Dict,
        job_name: str = 'default'
    ):
        """
        Schedule a single agent job.

        Args:
            agent_name: Agent name
            schedule: Cron expression
            goal: Task goal
            config: Job configuration
            job_name: Name for this specific job
        """
        if schedule == "on_demand":
            logger.info(f"Agent {agent_name} is on-demand only, not scheduling")
            return

        job_id = f"{agent_name}_{job_name}"

        # Create job function
        def job_func():
            self._execute_agent_task(
                agent_name=agent_name,
                goal=goal,
                config=config
            )

        # Schedule with APScheduler
        try:
            job = self.scheduler.add_job(
                func=job_func,
                trigger=CronTrigger.from_crontab(schedule, timezone=self.timezone),
                id=job_id,
                name=f"{agent_name} - {job_name}",
                replace_existing=True
            )

            self.jobs[job_id] = {
                'job': job,
                'agent': agent_name,
                'schedule': schedule,
                'goal': goal,
                'config': config
            }

            logger.info(f"Scheduled {job_id}: {schedule}")

        except Exception as e:
            logger.error(f"Failed to schedule {job_id}: {e}")

    # ==================== Job Execution ====================

    def _run_orchestrator_cycle(self):
        """Execute orchestrator coordination cycle."""
        logger.info("=" * 60)
        logger.info("CRON: Running orchestrator coordination cycle")
        logger.info("=" * 60)

        try:
            self.orchestrator.coordinate()
            logger.info("Orchestrator cycle completed successfully")
        except Exception as e:
            logger.error(f"Orchestrator cycle failed: {e}", exc_info=True)

    def _execute_agent_task(
        self,
        agent_name: str,
        goal: str,
        config: Dict
    ):
        """
        Execute an agent task.

        Args:
            agent_name: Agent name
            goal: Task goal
            config: Task configuration
        """
        logger.info(f"CRON: Executing {agent_name} task")
        logger.info(f"  Goal: {goal[:100]}...")

        try:
            # Get priority from config
            priority = config.get('priority', 50)

            # Create task in orchestrator's queue
            task = self.orchestrator.queue.add_task(
                agent_name=agent_name,
                task_type=TaskType.RESEARCH,
                goal=goal,
                urgency=priority,
                importance=priority,
                metadata={
                    'scheduled': True,
                    'cron_job': True,
                    'skill': config.get('skill'),
                    'delivery': config.get('delivery', 'telegram'),
                    'format': config.get('format', 'default')
                }
            )

            logger.info(f"  Task {task.id} created (priority: {priority})")

            # Execute immediately if high priority
            if priority >= 70:
                logger.info("  High priority - executing immediately")
                self.orchestrator._execute_task(task)

        except Exception as e:
            logger.error(f"Failed to execute {agent_name} task: {e}", exc_info=True)

    # ==================== Scheduler Control ====================

    def start(self):
        """Start the scheduler."""
        if self.scheduler.running:
            logger.warning("Scheduler already running")
            return

        self.scheduler.start()
        logger.info("Cron scheduler started")

        # Log next run times
        self._log_next_runs()

    def stop(self):
        """Stop the scheduler."""
        if not self.scheduler.running:
            logger.warning("Scheduler not running")
            return

        self.scheduler.shutdown(wait=True)
        logger.info("Cron scheduler stopped")

    def pause(self):
        """Pause the scheduler."""
        self.scheduler.pause()
        logger.info("Cron scheduler paused")

    def resume(self):
        """Resume the scheduler."""
        self.scheduler.resume()
        logger.info("Cron scheduler resumed")

    # ==================== Job Management ====================

    def pause_agent(self, agent_name: str):
        """Pause all jobs for an agent."""
        paused = 0
        for job_id, job_info in self.jobs.items():
            if job_info.get('agent') == agent_name:
                self.scheduler.pause_job(job_id)
                paused += 1

        logger.info(f"Paused {paused} jobs for {agent_name}")

    def resume_agent(self, agent_name: str):
        """Resume all jobs for an agent."""
        resumed = 0
        for job_id, job_info in self.jobs.items():
            if job_info.get('agent') == agent_name:
                self.scheduler.resume_job(job_id)
                resumed += 1

        logger.info(f"Resumed {resumed} jobs for {agent_name}")

    def trigger_job_now(self, job_id: str):
        """Manually trigger a job immediately."""
        if job_id not in self.jobs:
            logger.error(f"Job {job_id} not found")
            return False

        try:
            job = self.jobs[job_id]['job']
            job.modify(next_run_time=datetime.now(self.timezone))
            logger.info(f"Triggered job {job_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to trigger job {job_id}: {e}")
            return False

    # ==================== Monitoring ====================

    def _job_listener(self, event):
        """Listen for job events."""
        job_id = event.job_id

        if event.exception:
            logger.error(f"Job {job_id} failed: {event.exception}")
        else:
            logger.info(f"Job {job_id} executed successfully")

    def _log_next_runs(self):
        """Log next run times for all jobs."""
        logger.info("Next scheduled runs:")
        jobs_list = []

        for job_id, job_info in self.jobs.items():
            job = job_info['job']
            next_run = job.next_run_time

            if next_run:
                jobs_list.append((next_run, job_id, job.name))

        # Sort by next run time
        jobs_list.sort(key=lambda x: x[0])

        for next_run, job_id, job_name in jobs_list[:10]:  # Show next 10
            logger.info(f"  {next_run.strftime('%Y-%m-%d %H:%M:%S')} - {job_name}")

    def get_schedule_status(self) -> Dict:
        """Get status of all scheduled jobs."""
        status = {
            'running': self.scheduler.running,
            'total_jobs': len(self.jobs),
            'jobs': []
        }

        for job_id, job_info in self.jobs.items():
            job = job_info['job']
            status['jobs'].append({
                'id': job_id,
                'name': job.name,
                'next_run': job.next_run_time.isoformat() if job.next_run_time else None,
                'schedule': job_info.get('schedule'),
                'agent': job_info.get('agent'),
                'enabled': not job.next_run_time is None
            })

        return status

    # ==================== Configuration Management ====================

    def reload_config(self):
        """Reload configuration and reschedule jobs."""
        logger.info("Reloading configuration...")

        try:
            # Load new config
            self.config = self._load_config()

            # Remove all existing jobs
            for job_id in list(self.jobs.keys()):
                try:
                    self.scheduler.remove_job(job_id)
                except:
                    pass

            self.jobs.clear()

            # Reschedule
            self.schedule_all()

            logger.info("Configuration reloaded successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to reload configuration: {e}")
            return False

    # ==================== Cleanup ====================

    def shutdown(self):
        """Shutdown scheduler and orchestrator."""
        logger.info("Shutting down cron scheduler...")

        self.stop()
        self.orchestrator.shutdown()

        logger.info("Cron scheduler shutdown complete")


# ==================== Standalone Execution ====================

def run_scheduler_daemon(config_path: str = "cron_config.yaml"):
    """
    Run scheduler as a standalone daemon.

    Args:
        config_path: Path to cron config file
    """
    import signal
    import time

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    logger.info("Starting Hermes Autonomous Agent Scheduler")

    # Create scheduler
    scheduler = CronScheduler(config_path=config_path)

    # Schedule all jobs
    scheduler.schedule_all()

    # Start scheduler
    scheduler.start()

    # Signal handlers are managed by main thread
    # No signal handling in daemon thread
    logger.info("Scheduler running in daemon mode.")

    # Keep running
    try:
        while True:
            time.sleep(60)  # Sleep 1 minute between checks

            # Log status every hour
            if datetime.now().minute == 0:
                status = scheduler.get_schedule_status()
                logger.info(f"Status: {status['total_jobs']} jobs, running: {status['running']}")

    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Scheduler error: {e}", exc_info=True)
    finally:
        scheduler.shutdown()


if __name__ == "__main__":
    run_scheduler_daemon()
