"""
Priority Queue - Task Scheduling and Prioritization

Intelligent task scheduling system that balances urgency, importance,
resource costs, and user preferences to optimize agent activity.
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Task status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskType(Enum):
    """Task type enumeration."""
    RESEARCH = "research"
    MONITORING = "monitoring"
    NOTIFICATION = "notification"
    ANALYSIS = "analysis"
    COORDINATION = "coordination"


@dataclass
class Task:
    """
    Task data class with priority scoring.
    """
    id: int
    agent_name: str
    task_type: TaskType
    goal: str
    created_at: datetime = field(default_factory=datetime.now)

    # Priority factors
    urgency: int = 50  # 0-100 (deadline-driven)
    importance: int = 50  # 0-100 (impact-driven)
    user_interest: float = 0.5  # 0-1 (learned preference)
    novelty: float = 0.5  # 0-1 (information uniqueness)

    # Resource constraints
    estimated_cost: float = 0.0  # API cost estimate
    estimated_duration: int = 300  # seconds
    max_retries: int = 3

    # Execution tracking
    status: TaskStatus = TaskStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[str] = None
    retry_count: int = 0

    # Metadata
    metadata: Dict = field(default_factory=dict)

    @property
    def priority_score(self) -> float:
        """
        Calculate priority score based on multiple factors.

        Score = (urgency * 0.3) + (importance * 0.3) + (user_interest * 100 * 0.2)
                + (novelty * 100 * 0.1) - (cost_penalty * 0.1)

        Returns:
            Priority score (0-100+)
        """
        # Base score from urgency and importance
        base_score = (self.urgency * 0.3) + (self.importance * 0.3)

        # User interest boost
        interest_score = self.user_interest * 100 * 0.2

        # Novelty bonus
        novelty_score = self.novelty * 100 * 0.1

        # Cost penalty (higher cost = lower priority if budget tight)
        cost_penalty = min(self.estimated_cost * 2, 10)  # Cap at 10 points

        # Age bonus (older pending tasks get slight boost)
        age_hours = (datetime.now() - self.created_at).total_seconds() / 3600
        age_bonus = min(age_hours * 0.5, 10)  # Max 10 points for old tasks

        total_score = base_score + interest_score + novelty_score + age_bonus - cost_penalty

        return max(0, total_score)

    @property
    def is_overdue(self) -> bool:
        """Check if task is overdue based on creation time + expected duration."""
        if self.status != TaskStatus.PENDING:
            return False

        expected_completion = self.created_at + timedelta(seconds=self.estimated_duration * 2)
        return datetime.now() > expected_completion

    @property
    def can_retry(self) -> bool:
        """Check if task can be retried."""
        return self.retry_count < self.max_retries


class PriorityQueue:
    """
    Intelligent priority queue for task scheduling.

    Features:
    - Multi-factor priority scoring
    - Budget-aware scheduling
    - Agent load balancing
    - Deadline enforcement
    - Adaptive learning from outcomes
    """

    def __init__(
        self,
        knowledge_base,  # KnowledgeBase instance
        daily_budget: float = 50.0,  # USD per day
        max_concurrent_tasks: int = 3
    ):
        """
        Initialize priority queue.

        Args:
            knowledge_base: KnowledgeBase instance for persistence
            daily_budget: Maximum API spend per day (USD)
            max_concurrent_tasks: Max concurrent task execution
        """
        self.kb = knowledge_base
        self.daily_budget = daily_budget
        self.max_concurrent_tasks = max_concurrent_tasks

        # Runtime state
        self.tasks: Dict[int, Task] = {}
        self.running_tasks: List[int] = []

        # Budget tracking
        self.budget_used_today = 0.0
        self.budget_reset_at = datetime.now().replace(hour=0, minute=0, second=0) + timedelta(days=1)

        # Load tracking per agent
        self.agent_load: Dict[str, int] = {}

        logger.info(f"PriorityQueue initialized: ${daily_budget}/day budget, {max_concurrent_tasks} max concurrent")

    # ==================== Task Management ====================

    def add_task(
        self,
        agent_name: str,
        task_type: TaskType,
        goal: str,
        urgency: int = 50,
        importance: int = 50,
        user_interest: float = 0.5,
        novelty: float = 0.5,
        estimated_cost: float = 0.0,
        estimated_duration: int = 300,
        metadata: Optional[Dict] = None
    ) -> Task:
        """
        Add a new task to the queue.

        Args:
            agent_name: Assigned agent
            task_type: Type of task
            goal: Task goal/description
            urgency: Urgency score (0-100)
            importance: Importance score (0-100)
            user_interest: User interest level (0-1)
            novelty: Novelty score (0-1)
            estimated_cost: Estimated API cost (USD)
            estimated_duration: Estimated duration (seconds)
            metadata: Additional metadata

        Returns:
            Created Task object
        """
        # Store in database
        task_id = self.kb.create_task(
            agent_name=agent_name,
            task_type=task_type.value,
            goal=goal,
            priority=int((urgency + importance) / 2),  # Simple initial priority
            metadata=metadata or {}
        )

        # Create Task object
        task = Task(
            id=task_id,
            agent_name=agent_name,
            task_type=task_type,
            goal=goal,
            urgency=urgency,
            importance=importance,
            user_interest=user_interest,
            novelty=novelty,
            estimated_cost=estimated_cost,
            estimated_duration=estimated_duration,
            metadata=metadata or {}
        )

        self.tasks[task_id] = task
        logger.info(f"Task {task_id} added: {goal[:50]}... (priority: {task.priority_score:.1f})")

        return task

    def get_next_task(
        self,
        agent_name: Optional[str] = None,
        respect_budget: bool = True
    ) -> Optional[Task]:
        """
        Get highest priority task that meets constraints.

        Args:
            agent_name: Only get tasks for this agent (None = any)
            respect_budget: Enforce daily budget limit

        Returns:
            Next Task to execute, or None
        """
        # Reset budget if new day
        self._check_budget_reset()

        # Filter pending tasks
        pending = [
            task for task in self.tasks.values()
            if task.status == TaskStatus.PENDING
            and (agent_name is None or task.agent_name == agent_name)
        ]

        if not pending:
            return None

        # Check concurrent task limit
        if len(self.running_tasks) >= self.max_concurrent_tasks:
            logger.debug(f"Max concurrent tasks reached ({self.max_concurrent_tasks})")
            return None

        # Filter by budget if enabled
        if respect_budget:
            remaining_budget = self.daily_budget - self.budget_used_today
            pending = [t for t in pending if t.estimated_cost <= remaining_budget]

            if not pending:
                logger.warning(f"No tasks within remaining budget: ${remaining_budget:.2f}")
                return None

        # Sort by priority score
        pending.sort(key=lambda t: t.priority_score, reverse=True)

        # Return highest priority task
        return pending[0]

    def start_task(self, task_id: int) -> bool:
        """
        Mark task as running.

        Args:
            task_id: Task ID

        Returns:
            True if started successfully
        """
        if task_id not in self.tasks:
            logger.error(f"Task {task_id} not found")
            return False

        task = self.tasks[task_id]

        if task.status != TaskStatus.PENDING:
            logger.warning(f"Task {task_id} not pending (status: {task.status})")
            return False

        # Update task
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now()
        self.running_tasks.append(task_id)

        # Update agent load
        self.agent_load[task.agent_name] = self.agent_load.get(task.agent_name, 0) + 1

        # Update database
        self.kb.update_task_status(task_id, "running")

        logger.info(f"Task {task_id} started: {task.goal[:50]}...")
        return True

    def complete_task(
        self,
        task_id: int,
        result: str,
        actual_cost: Optional[float] = None,
        success: bool = True
    ) -> bool:
        """
        Mark task as completed.

        Args:
            task_id: Task ID
            result: Task result/output
            actual_cost: Actual cost incurred
            success: Whether task succeeded

        Returns:
            True if completed successfully
        """
        if task_id not in self.tasks:
            logger.error(f"Task {task_id} not found")
            return False

        task = self.tasks[task_id]

        # Update task
        task.status = TaskStatus.COMPLETED if success else TaskStatus.FAILED
        task.completed_at = datetime.now()
        task.result = result

        # Update budget
        cost = actual_cost if actual_cost is not None else task.estimated_cost
        self.budget_used_today += cost

        # Update agent load
        if task_id in self.running_tasks:
            self.running_tasks.remove(task_id)
        self.agent_load[task.agent_name] = max(0, self.agent_load.get(task.agent_name, 1) - 1)

        # Update database
        self.kb.update_task_status(
            task_id,
            "completed" if success else "failed",
            result=result
        )

        # Learn from outcome
        self._learn_from_task(task, success, cost)

        status_str = "completed" if success else "failed"
        logger.info(f"Task {task_id} {status_str}: cost ${cost:.2f}, total today ${self.budget_used_today:.2f}")

        return True

    def retry_task(self, task_id: int) -> bool:
        """
        Retry a failed task.

        Args:
            task_id: Task ID

        Returns:
            True if retry queued
        """
        if task_id not in self.tasks:
            return False

        task = self.tasks[task_id]

        if not task.can_retry:
            logger.warning(f"Task {task_id} cannot retry (max retries reached)")
            return False

        task.status = TaskStatus.PENDING
        task.retry_count += 1
        task.started_at = None
        task.completed_at = None

        if task_id in self.running_tasks:
            self.running_tasks.remove(task_id)

        logger.info(f"Task {task_id} queued for retry ({task.retry_count}/{task.max_retries})")
        return True

    # ==================== Budget Management ====================

    def _check_budget_reset(self):
        """Reset daily budget if new day."""
        if datetime.now() >= self.budget_reset_at:
            logger.info(f"Daily budget reset: ${self.budget_used_today:.2f} spent yesterday")
            self.budget_used_today = 0.0
            self.budget_reset_at = datetime.now().replace(hour=0, minute=0, second=0) + timedelta(days=1)

    def get_budget_status(self) -> Dict:
        """Get current budget status."""
        remaining = self.daily_budget - self.budget_used_today
        percent_used = (self.budget_used_today / self.daily_budget) * 100

        return {
            "daily_budget": self.daily_budget,
            "used_today": self.budget_used_today,
            "remaining": remaining,
            "percent_used": percent_used,
            "resets_at": self.budget_reset_at.isoformat()
        }

    def adjust_budget(self, new_budget: float):
        """Adjust daily budget."""
        old_budget = self.daily_budget
        self.daily_budget = new_budget
        logger.info(f"Daily budget adjusted: ${old_budget:.2f} -> ${new_budget:.2f}")

    # ==================== Agent Load Balancing ====================

    def get_agent_load(self, agent_name: str) -> int:
        """Get current task load for agent."""
        return self.agent_load.get(agent_name, 0)

    def get_least_loaded_agent(self, agents: List[str]) -> str:
        """Get agent with lowest current load."""
        loads = [(agent, self.get_agent_load(agent)) for agent in agents]
        loads.sort(key=lambda x: x[1])
        return loads[0][0] if loads else agents[0]

    # ==================== Learning & Optimization ====================

    def _learn_from_task(self, task: Task, success: bool, actual_cost: float):
        """
        Learn from task outcomes to improve future scheduling.

        Args:
            task: Completed task
            success: Whether task succeeded
            actual_cost: Actual cost incurred
        """
        # Update user preferences if applicable
        if task.metadata.get("topic"):
            topic = task.metadata["topic"]
            engagement = 0.1 if success else -0.1
            self.kb.update_user_preference(topic, engagement)

        # Log cost accuracy for future estimation
        if actual_cost != task.estimated_cost:
            cost_diff = actual_cost - task.estimated_cost
            logger.debug(f"Cost estimation off by ${cost_diff:.2f} for {task.task_type.value}")

        # TODO: Implement more sophisticated learning
        # - Track which task types succeed/fail
        # - Learn optimal times to run certain tasks
        # - Adjust priority scoring weights based on outcomes

    # ==================== Statistics & Monitoring ====================

    def get_stats(self) -> Dict:
        """Get queue statistics."""
        pending = sum(1 for t in self.tasks.values() if t.status == TaskStatus.PENDING)
        running = len(self.running_tasks)
        completed = sum(1 for t in self.tasks.values() if t.status == TaskStatus.COMPLETED)
        failed = sum(1 for t in self.tasks.values() if t.status == TaskStatus.FAILED)

        return {
            "total_tasks": len(self.tasks),
            "pending": pending,
            "running": running,
            "completed": completed,
            "failed": failed,
            "budget_used": self.budget_used_today,
            "budget_remaining": self.daily_budget - self.budget_used_today,
            "agent_loads": dict(self.agent_load)
        }

    def get_overdue_tasks(self) -> List[Task]:
        """Get list of overdue tasks."""
        return [task for task in self.tasks.values() if task.is_overdue]

    def get_high_priority_tasks(self, threshold: float = 70.0) -> List[Task]:
        """Get tasks above priority threshold."""
        tasks = [
            task for task in self.tasks.values()
            if task.status == TaskStatus.PENDING and task.priority_score >= threshold
        ]
        tasks.sort(key=lambda t: t.priority_score, reverse=True)
        return tasks

    # ==================== Cleanup ====================

    def cleanup_old_tasks(self, days: int = 30):
        """Remove completed tasks older than N days."""
        cutoff = datetime.now() - timedelta(days=days)
        to_remove = []

        for task_id, task in self.tasks.items():
            if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
                if task.completed_at and task.completed_at < cutoff:
                    to_remove.append(task_id)

        for task_id in to_remove:
            del self.tasks[task_id]

        if to_remove:
            logger.info(f"Cleaned up {len(to_remove)} old tasks")

        return len(to_remove)
