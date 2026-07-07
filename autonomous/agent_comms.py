"""
Agent Communications - Inter-Agent Messaging via Redis

Provides pub/sub messaging system for agents to communicate discoveries,
questions, alerts, and coordinate activities.
"""

import os
import redis
import json
import logging
from typing import Dict, List, Callable, Optional, Any
from datetime import datetime
from threading import Thread
import time

logger = logging.getLogger(__name__)


class AgentCommunications:
    """
    Redis-based pub/sub system for inter-agent communication.

    Channels:
    - agent:discoveries - Share new findings
    - agent:questions - Ask other agents for help
    - agent:tasks - Delegate or coordinate tasks
    - agent:alerts - Urgent notifications
    """

    # Channel definitions
    CHANNEL_DISCOVERIES = "agent:discoveries"
    CHANNEL_QUESTIONS = "agent:questions"
    CHANNEL_TASKS = "agent:tasks"
    CHANNEL_ALERTS = "agent:alerts"

    ALL_CHANNELS = [
        CHANNEL_DISCOVERIES,
        CHANNEL_QUESTIONS,
        CHANNEL_TASKS,
        CHANNEL_ALERTS
    ]

    def __init__(self, redis_url: Optional[str] = None):
        """
        Initialize Redis connection.

        Args:
            redis_url: Redis connection string (defaults to REDIS_URL env var)
        """
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")

        try:
            self.client = redis.from_url(
                self.redis_url,
                decode_responses=True,
                socket_connect_timeout=5
            )
            self.pubsub = self.client.pubsub()
            logger.info("Connected to Redis for agent communications")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise

        self.subscribers: Dict[str, List[Callable]] = {}
        self.listener_thread: Optional[Thread] = None
        self.listening = False

    # ==================== Publishing Methods ====================

    def publish_discovery(
        self,
        agent_name: str,
        topic: str,
        content: str,
        relevance: float = 0.5,
        metadata: Optional[Dict] = None
    ) -> int:
        """
        Publish a discovery to other agents.

        Args:
            agent_name: Name of discovering agent
            topic: Topic/category
            content: Discovery content
            relevance: Relevance score (0-1)
            metadata: Additional data

        Returns:
            Number of subscribers who received the message
        """
        message = {
            "type": "discovery",
            "agent": agent_name,
            "topic": topic,
            "content": content,
            "relevance": relevance,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }

        return self._publish(self.CHANNEL_DISCOVERIES, message)

    def publish_question(
        self,
        agent_name: str,
        question: str,
        context: Optional[str] = None,
        target_agent: Optional[str] = None,
        urgency: str = "normal"
    ) -> int:
        """
        Ask a question to other agents.

        Args:
            agent_name: Name of asking agent
            question: The question
            context: Additional context
            target_agent: Specific agent to ask (None = broadcast)
            urgency: 'low', 'normal', 'high', 'urgent'

        Returns:
            Number of subscribers
        """
        message = {
            "type": "question",
            "agent": agent_name,
            "question": question,
            "context": context,
            "target": target_agent,
            "urgency": urgency,
            "timestamp": datetime.now().isoformat()
        }

        return self._publish(self.CHANNEL_QUESTIONS, message)

    def publish_task(
        self,
        agent_name: str,
        task_description: str,
        assigned_to: Optional[str] = None,
        priority: int = 50,
        metadata: Optional[Dict] = None
    ) -> int:
        """
        Publish a task for coordination.

        Args:
            agent_name: Name of publishing agent
            task_description: Task details
            assigned_to: Specific agent assignment (None = any available)
            priority: Priority (0-100)
            metadata: Additional task data

        Returns:
            Number of subscribers
        """
        message = {
            "type": "task",
            "agent": agent_name,
            "task": task_description,
            "assigned_to": assigned_to,
            "priority": priority,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }

        return self._publish(self.CHANNEL_TASKS, message)

    def publish_alert(
        self,
        agent_name: str,
        alert_type: str,
        message_text: str,
        severity: str = "info",
        metadata: Optional[Dict] = None
    ) -> int:
        """
        Publish an alert to other agents.

        Args:
            agent_name: Name of alerting agent
            alert_type: Type of alert
            message_text: Alert message
            severity: 'info', 'warning', 'error', 'critical'
            metadata: Additional data

        Returns:
            Number of subscribers
        """
        message = {
            "type": "alert",
            "agent": agent_name,
            "alert_type": alert_type,
            "message": message_text,
            "severity": severity,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }

        return self._publish(self.CHANNEL_ALERTS, message)

    def _publish(self, channel: str, message: Dict) -> int:
        """Internal publish method."""
        try:
            message_json = json.dumps(message)
            count = self.client.publish(channel, message_json)
            logger.debug(f"Published to {channel}: {message.get('type')} from {message.get('agent')}")
            return count
        except Exception as e:
            logger.error(f"Failed to publish to {channel}: {e}")
            return 0

    # ==================== Subscription Methods ====================

    def subscribe(
        self,
        channel: str,
        callback: Callable[[Dict], None],
        agent_name: Optional[str] = None
    ):
        """
        Subscribe to a channel with callback.

        Args:
            channel: Channel to subscribe to
            callback: Function to call on message (receives message dict)
            agent_name: Optional filter for specific agent messages
        """
        if channel not in self.subscribers:
            self.subscribers[channel] = []
            self.pubsub.subscribe(channel)

        # Wrap callback with optional agent filter
        def wrapped_callback(message: Dict):
            if agent_name and message.get("agent") != agent_name:
                return  # Skip if not from specified agent
            try:
                callback(message)
            except Exception as e:
                logger.error(f"Callback error for {channel}: {e}")

        self.subscribers[channel].append(wrapped_callback)
        logger.info(f"Subscribed to {channel}" + (f" (agent: {agent_name})" if agent_name else ""))

    def subscribe_discoveries(self, callback: Callable[[Dict], None], topic: Optional[str] = None):
        """
        Subscribe to discoveries, optionally filtered by topic.

        Args:
            callback: Function to call on discovery
            topic: Optional topic filter
        """
        def filtered_callback(message: Dict):
            if topic and message.get("topic") != topic:
                return
            callback(message)

        self.subscribe(self.CHANNEL_DISCOVERIES, filtered_callback)

    def subscribe_questions(self, callback: Callable[[Dict], None], agent_name: str):
        """
        Subscribe to questions, filtered for this agent.

        Args:
            callback: Function to call on question
            agent_name: This agent's name (to filter relevant questions)
        """
        def filtered_callback(message: Dict):
            target = message.get("target")
            if target and target != agent_name:
                return  # Not for this agent
            callback(message)

        self.subscribe(self.CHANNEL_QUESTIONS, filtered_callback)

    def subscribe_tasks(self, callback: Callable[[Dict], None], agent_name: str):
        """
        Subscribe to tasks assigned to this agent.

        Args:
            callback: Function to call on task
            agent_name: This agent's name
        """
        def filtered_callback(message: Dict):
            assigned = message.get("assigned_to")
            if assigned and assigned != agent_name:
                return  # Not for this agent
            callback(message)

        self.subscribe(self.CHANNEL_TASKS, filtered_callback)

    def subscribe_alerts(self, callback: Callable[[Dict], None], min_severity: str = "info"):
        """
        Subscribe to alerts with minimum severity.

        Args:
            callback: Function to call on alert
            min_severity: Minimum severity to receive
        """
        severity_levels = {"info": 0, "warning": 1, "error": 2, "critical": 3}
        min_level = severity_levels.get(min_severity, 0)

        def filtered_callback(message: Dict):
            severity = message.get("severity", "info")
            if severity_levels.get(severity, 0) >= min_level:
                callback(message)

        self.subscribe(self.CHANNEL_ALERTS, filtered_callback)

    # ==================== Listener Thread ====================

    def start_listening(self):
        """Start background thread to listen for messages."""
        if self.listening:
            logger.warning("Already listening")
            return

        self.listening = True
        self.listener_thread = Thread(target=self._listen_loop, daemon=True)
        self.listener_thread.start()
        logger.info("Started listening for agent messages")

    def stop_listening(self):
        """Stop background listener thread."""
        if not self.listening:
            return

        self.listening = False
        if self.listener_thread:
            self.listener_thread.join(timeout=5)
        logger.info("Stopped listening for agent messages")

    def _listen_loop(self):
        """Background loop to process messages."""
        while self.listening:
            try:
                message = self.pubsub.get_message(timeout=1.0)
                if message and message['type'] == 'message':
                    channel = message['channel']
                    data = json.loads(message['data'])

                    # Call all subscribers for this channel
                    if channel in self.subscribers:
                        for callback in self.subscribers[channel]:
                            try:
                                callback(data)
                            except Exception as e:
                                logger.error(f"Callback error: {e}")

            except Exception as e:
                if self.listening:  # Only log if not intentionally stopped
                    logger.error(f"Listener error: {e}")
                    time.sleep(1)  # Brief pause before retrying

    # ==================== Direct Messaging ====================

    def send_direct_message(
        self,
        from_agent: str,
        to_agent: str,
        message: str,
        message_type: str = "general",
        metadata: Optional[Dict] = None
    ):
        """
        Send a direct message to a specific agent (via Redis list).

        Args:
            from_agent: Sender
            to_agent: Recipient
            message: Message content
            message_type: Type of message
            metadata: Additional data
        """
        key = f"agent:inbox:{to_agent}"
        message_data = {
            "from": from_agent,
            "to": to_agent,
            "type": message_type,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }

        try:
            self.client.lpush(key, json.dumps(message_data))
            # Set TTL of 7 days on inbox
            self.client.expire(key, 7 * 24 * 60 * 60)
            logger.debug(f"Direct message sent: {from_agent} -> {to_agent}")
        except Exception as e:
            logger.error(f"Failed to send direct message: {e}")

    def read_inbox(self, agent_name: str, max_messages: int = 10) -> List[Dict]:
        """
        Read messages from agent's inbox.

        Args:
            agent_name: Agent name
            max_messages: Max messages to retrieve

        Returns:
            List of messages
        """
        key = f"agent:inbox:{agent_name}"
        messages = []

        try:
            # Get messages (non-blocking)
            for _ in range(max_messages):
                msg_json = self.client.rpop(key)
                if not msg_json:
                    break
                messages.append(json.loads(msg_json))

            if messages:
                logger.debug(f"Read {len(messages)} messages for {agent_name}")
            return messages
        except Exception as e:
            logger.error(f"Failed to read inbox: {e}")
            return []

    # ==================== Presence & Coordination ====================

    def set_agent_status(
        self,
        agent_name: str,
        status: str,
        current_task: Optional[str] = None,
        ttl_seconds: int = 300
    ):
        """
        Set agent's current status (with auto-expiration).

        Args:
            agent_name: Agent name
            status: 'idle', 'busy', 'offline'
            current_task: Current task description
            ttl_seconds: Status expires after this (default 5 min)
        """
        key = f"agent:status:{agent_name}"
        status_data = {
            "status": status,
            "task": current_task,
            "updated_at": datetime.now().isoformat()
        }

        try:
            self.client.setex(key, ttl_seconds, json.dumps(status_data))
        except Exception as e:
            logger.error(f"Failed to set agent status: {e}")

    def get_agent_status(self, agent_name: str) -> Optional[Dict]:
        """Get agent's current status."""
        key = f"agent:status:{agent_name}"
        try:
            data = self.client.get(key)
            return json.loads(data) if data else None
        except Exception as e:
            logger.error(f"Failed to get agent status: {e}")
            return None

    def get_active_agents(self) -> List[str]:
        """Get list of currently active agents."""
        try:
            keys = self.client.keys("agent:status:*")
            return [key.split(":")[-1] for key in keys]
        except Exception as e:
            logger.error(f"Failed to get active agents: {e}")
            return []

    # ==================== Utility Methods ====================

    def clear_all(self):
        """Clear all agent communication data (use carefully!)."""
        try:
            # Clear pubsub channels (can't actually clear, just unsubscribe)
            self.pubsub.unsubscribe()

            # Clear inboxes and statuses
            keys = self.client.keys("agent:*")
            if keys:
                self.client.delete(*keys)

            logger.info("Cleared all agent communication data")
        except Exception as e:
            logger.error(f"Failed to clear data: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about agent communications."""
        stats = {
            "active_agents": len(self.get_active_agents()),
            "subscribed_channels": len(self.subscribers),
            "listening": self.listening
        }

        try:
            # Get channel subscriber counts
            for channel in self.ALL_CHANNELS:
                count = self.client.pubsub_numsub(channel)[0][1]
                stats[f"{channel}_subscribers"] = count
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")

        return stats

    def close(self):
        """Close Redis connections."""
        self.stop_listening()
        if self.pubsub:
            self.pubsub.close()
        if self.client:
            self.client.close()
        logger.info("Agent communications closed")


# ==================== Helper Functions ====================

def example_discovery_handler(message: Dict):
    """Example handler for discoveries."""
    print(f"📢 Discovery from {message['agent']}: {message['topic']}")
    print(f"   {message['content'][:100]}...")


def example_question_handler(message: Dict):
    """Example handler for questions."""
    print(f"❓ Question from {message['agent']}: {message['question']}")


def example_usage():
    """Example usage of AgentCommunications."""
    comms = AgentCommunications()

    # Subscribe to discoveries
    comms.subscribe_discoveries(example_discovery_handler)

    # Subscribe to questions for a specific agent
    comms.subscribe_questions(example_question_handler, "ai_researcher")

    # Start listening
    comms.start_listening()

    # Publish a discovery
    comms.publish_discovery(
        agent_name="ai_researcher",
        topic="AI/ML",
        content="New GPT-5 paper released on ArXiv",
        relevance=0.9
    )

    # Publish a question
    comms.publish_question(
        agent_name="orchestrator",
        question="Has anyone seen information about the new OpenAI API pricing?",
        target_agent="software_dev"
    )

    # Keep running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        comms.stop_listening()
        comms.close()


if __name__ == "__main__":
    # Example usage
    example_usage()
