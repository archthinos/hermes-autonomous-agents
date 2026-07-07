"""
Autonomous Multi-Agent System Core

This package contains the core components for the autonomous multi-agent system:
- Orchestrator: Main coordinator and task manager
- Goal Generator: Proactive task and goal creation
- Priority Queue: Task scheduling and prioritization
- Agent Communications: Inter-agent messaging via Redis
- Knowledge Base: Shared PostgreSQL knowledge repository
- Novelty Detector: Deduplication and content uniqueness scoring
"""

__version__ = "1.0.0"

from .orchestrator import Orchestrator
from .goal_generator import GoalGenerator
from .priority_queue import PriorityQueue
from .agent_comms import AgentCommunications
from .knowledge_base import KnowledgeBase
from .novelty_detector import NoveltyDetector

__all__ = [
    "Orchestrator",
    "GoalGenerator",
    "PriorityQueue",
    "AgentCommunications",
    "KnowledgeBase",
    "NoveltyDetector",
]
