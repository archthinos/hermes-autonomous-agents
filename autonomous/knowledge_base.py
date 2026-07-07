"""
Knowledge Base - Shared PostgreSQL Repository

Provides interface to shared knowledge across all agents.
Stores discoveries, research results, user preferences, and task history.
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor, Json
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
import logging

logger = logging.getLogger(__name__)


class KnowledgeBase:
    """
    Shared knowledge repository for multi-agent system.
    Uses PostgreSQL with pg

vector extension for embeddings.
    """

    def __init__(self, database_url: Optional[str] = None):
        """
        Initialize connection to PostgreSQL database.

        Args:
            database_url: PostgreSQL connection string (defaults to DATABASE_URL env var)
        """
        self.database_url = database_url or os.getenv("DATABASE_URL")
        if not self.database_url:
            raise ValueError("DATABASE_URL not set")

        self.conn = None
        self._connect()
        self._ensure_schema()

    def _connect(self):
        """Establish database connection with auto-reconnect."""
        try:
            self.conn = psycopg2.connect(
                self.database_url,
                cursor_factory=RealDictCursor,
                connect_timeout=10
            )
            self.conn.autocommit = True
            logger.info("Connected to knowledge base")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise

    def _ensure_schema(self):
        """Create tables if they don't exist."""
        schema = """
        -- Enable pgvector extension for embeddings (if available)
        CREATE EXTENSION IF NOT EXISTS vector;

        -- Agent knowledge: cross-agent shared discoveries
        CREATE TABLE IF NOT EXISTS agent_knowledge (
            id SERIAL PRIMARY KEY,
            agent_name VARCHAR(50) NOT NULL,
            topic VARCHAR(100) NOT NULL,
            content TEXT NOT NULL,
            embeddings vector(1536),  -- OpenAI embeddings dimension
            relevance_score FLOAT DEFAULT 0.0,
            user_engagement FLOAT DEFAULT 0.0,  -- Track user reactions
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,
            metadata JSONB DEFAULT '{}'::jsonb
        );

        CREATE INDEX IF NOT EXISTS idx_agent_knowledge_topic ON agent_knowledge(topic);
        CREATE INDEX IF NOT EXISTS idx_agent_knowledge_agent ON agent_knowledge(agent_name);
        CREATE INDEX IF NOT EXISTS idx_agent_knowledge_created ON agent_knowledge(created_at DESC);

        -- Task queue: priority task scheduling
        CREATE TABLE IF NOT EXISTS task_queue (
            id SERIAL PRIMARY KEY,
            agent_name VARCHAR(50) NOT NULL,
            task_type VARCHAR(50) NOT NULL,
            goal TEXT NOT NULL,
            priority INT DEFAULT 50,
            status VARCHAR(20) DEFAULT 'pending',  -- pending, running, completed, failed
            result TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            started_at TIMESTAMP,
            completed_at TIMESTAMP,
            metadata JSONB DEFAULT '{}'::jsonb
        );

        CREATE INDEX IF NOT EXISTS idx_task_queue_status ON task_queue(status);
        CREATE INDEX IF NOT EXISTS idx_task_queue_priority ON task_queue(priority DESC);
        CREATE INDEX IF NOT EXISTS idx_task_queue_agent ON task_queue(agent_name);

        -- Research cache: deduplication and query caching
        CREATE TABLE IF NOT EXISTS research_cache (
            id SERIAL PRIMARY KEY,
            query_hash VARCHAR(64) UNIQUE NOT NULL,
            query TEXT NOT NULL,
            results JSONB NOT NULL,
            embeddings vector(1536),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            accessed_count INT DEFAULT 1,
            last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_research_cache_hash ON research_cache(query_hash);
        CREATE INDEX IF NOT EXISTS idx_research_cache_created ON research_cache(created_at DESC);

        -- User preferences: learning user interests
        CREATE TABLE IF NOT EXISTS user_preferences (
            id SERIAL PRIMARY KEY,
            topic VARCHAR(100) UNIQUE NOT NULL,
            engagement_score FLOAT DEFAULT 0.0,  -- Based on reactions, replies
            frequency VARCHAR(20) DEFAULT 'medium',  -- high, medium, low
            notification_count INT DEFAULT 0,
            positive_reactions INT DEFAULT 0,
            negative_reactions INT DEFAULT 0,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            metadata JSONB DEFAULT '{}'::jsonb
        );

        CREATE INDEX IF NOT EXISTS idx_user_prefs_topic ON user_preferences(topic);
        CREATE INDEX IF NOT EXISTS idx_user_prefs_engagement ON user_preferences(engagement_score DESC);
        """

        try:
            with self.conn.cursor() as cur:
                cur.execute(schema)
            logger.info("Schema initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize schema: {e}")
            raise

    # ==================== Agent Knowledge Methods ====================

    def store_knowledge(
        self,
        agent_name: str,
        topic: str,
        content: str,
        relevance_score: float = 0.0,
        embeddings: Optional[List[float]] = None,
        expires_in_days: int = 30,
        metadata: Optional[Dict] = None
    ) -> int:
        """
        Store a piece of knowledge discovered by an agent.

        Args:
            agent_name: Name of agent storing knowledge
            topic: Topic/category
            content: The actual content/discovery
            relevance_score: Initial relevance (0-1)
            embeddings: Optional embedding vector
            expires_in_days: Auto-expire after N days
            metadata: Additional JSON metadata

        Returns:
            ID of stored knowledge
        """
        expires_at = datetime.now() + timedelta(days=expires_in_days)
        metadata = metadata or {}

        query = """
        INSERT INTO agent_knowledge
        (agent_name, topic, content, relevance_score, embeddings, expires_at, metadata)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING id
        """

        try:
            with self.conn.cursor() as cur:
                cur.execute(query, (
                    agent_name, topic, content, relevance_score,
                    embeddings, expires_at, Json(metadata)
                ))
                result = cur.fetchone()
                return result['id']
        except Exception as e:
            logger.error(f"Failed to store knowledge: {e}")
            raise

    def search_knowledge(
        self,
        topic: Optional[str] = None,
        agent_name: Optional[str] = None,
        min_relevance: float = 0.0,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search stored knowledge.

        Args:
            topic: Filter by topic
            agent_name: Filter by agent
            min_relevance: Minimum relevance score
            limit: Max results

        Returns:
            List of knowledge entries
        """
        query = """
        SELECT * FROM agent_knowledge
        WHERE
            (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)
            AND relevance_score >= %s
        """
        params = [min_relevance]

        if topic:
            query += " AND topic = %s"
            params.append(topic)

        if agent_name:
            query += " AND agent_name = %s"
            params.append(agent_name)

        query += " ORDER BY relevance_score DESC, created_at DESC LIMIT %s"
        params.append(limit)

        try:
            with self.conn.cursor() as cur:
                cur.execute(query, params)
                return cur.fetchall()
        except Exception as e:
            logger.error(f"Failed to search knowledge: {e}")
            return []

    def update_knowledge_engagement(self, knowledge_id: int, engagement_delta: float):
        """Update knowledge entry based on user engagement."""
        query = """
        UPDATE agent_knowledge
        SET user_engagement = user_engagement + %s,
            relevance_score = LEAST(1.0, relevance_score + (%s * 0.1))
        WHERE id = %s
        """
        try:
            with self.conn.cursor() as cur:
                cur.execute(query, (engagement_delta, engagement_delta, knowledge_id))
        except Exception as e:
            logger.error(f"Failed to update engagement: {e}")

    # ==================== Task Queue Methods ====================

    def create_task(
        self,
        agent_name: str,
        task_type: str,
        goal: str,
        priority: int = 50,
        metadata: Optional[Dict] = None
    ) -> int:
        """
        Create a new task in the queue.

        Args:
            agent_name: Agent responsible for task
            task_type: Type of task
            goal: Task goal/description
            priority: Priority (0-100, higher = more urgent)
            metadata: Additional JSON metadata

        Returns:
            Task ID
        """
        metadata = metadata or {}

        query = """
        INSERT INTO task_queue (agent_name, task_type, goal, priority, metadata)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id
        """

        try:
            with self.conn.cursor() as cur:
                cur.execute(query, (agent_name, task_type, goal, priority, Json(metadata)))
                result = cur.fetchone()
                logger.info(f"Created task {result['id']} for {agent_name}: {goal[:50]}...")
                return result['id']
        except Exception as e:
            logger.error(f"Failed to create task: {e}")
            raise

    def get_next_task(self, agent_name: Optional[str] = None) -> Optional[Dict]:
        """
        Get highest priority pending task.

        Args:
            agent_name: If provided, only get tasks for this agent

        Returns:
            Task dict or None
        """
        query = """
        SELECT * FROM task_queue
        WHERE status = 'pending'
        """
        params = []

        if agent_name:
            query += " AND agent_name = %s"
            params.append(agent_name)

        query += " ORDER BY priority DESC, created_at ASC LIMIT 1"

        try:
            with self.conn.cursor() as cur:
                cur.execute(query, params)
                return cur.fetchone()
        except Exception as e:
            logger.error(f"Failed to get next task: {e}")
            return None

    def update_task_status(
        self,
        task_id: int,
        status: str,
        result: Optional[str] = None
    ):
        """Update task status."""
        query = """
        UPDATE task_queue
        SET status = %s,
            result = %s,
            started_at = CASE WHEN status = 'running' AND started_at IS NULL
                              THEN CURRENT_TIMESTAMP ELSE started_at END,
            completed_at = CASE WHEN status IN ('completed', 'failed')
                                THEN CURRENT_TIMESTAMP ELSE completed_at END
        WHERE id = %s
        """
        try:
            with self.conn.cursor() as cur:
                cur.execute(query, (status, result, task_id))
                logger.info(f"Task {task_id} status updated to {status}")
        except Exception as e:
            logger.error(f"Failed to update task status: {e}")

    # ==================== Research Cache Methods ====================

    def cache_research(
        self,
        query: str,
        results: Dict,
        embeddings: Optional[List[float]] = None
    ) -> int:
        """Cache research results to avoid duplicate searches."""
        import hashlib
        query_hash = hashlib.sha256(query.encode()).hexdigest()

        query_sql = """
        INSERT INTO research_cache (query_hash, query, results, embeddings)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (query_hash) DO UPDATE
        SET accessed_count = research_cache.accessed_count + 1,
            last_accessed = CURRENT_TIMESTAMP
        RETURNING id
        """

        try:
            with self.conn.cursor() as cur:
                cur.execute(query_sql, (query_hash, query, Json(results), embeddings))
                result = cur.fetchone()
                return result['id']
        except Exception as e:
            logger.error(f"Failed to cache research: {e}")
            raise

    def get_cached_research(self, query: str, max_age_hours: int = 24) -> Optional[Dict]:
        """Retrieve cached research if recent enough."""
        import hashlib
        query_hash = hashlib.sha256(query.encode()).hexdigest()

        query_sql = """
        SELECT * FROM research_cache
        WHERE query_hash = %s
          AND created_at > CURRENT_TIMESTAMP - INTERVAL '%s hours'
        ORDER BY created_at DESC
        LIMIT 1
        """

        try:
            with self.conn.cursor() as cur:
                cur.execute(query_sql, (query_hash, max_age_hours))
                result = cur.fetchone()
                if result:
                    # Update access stats
                    self.conn.cursor().execute(
                        "UPDATE research_cache SET accessed_count = accessed_count + 1, "
                        "last_accessed = CURRENT_TIMESTAMP WHERE id = %s",
                        (result['id'],)
                    )
                return result
        except Exception as e:
            logger.error(f"Failed to get cached research: {e}")
            return None

    # ==================== User Preferences Methods ====================

    def update_user_preference(
        self,
        topic: str,
        engagement_delta: float,
        reaction_type: Optional[str] = None
    ):
        """
        Update user preference based on engagement.

        Args:
            topic: Topic to update
            engagement_delta: Change in engagement score (-1 to +1)
            reaction_type: 'positive', 'negative', or None
        """
        query = """
        INSERT INTO user_preferences (topic, engagement_score, notification_count, positive_reactions, negative_reactions)
        VALUES (%s, %s, 1, %s, %s)
        ON CONFLICT (topic) DO UPDATE
        SET engagement_score = user_preferences.engagement_score + %s,
            notification_count = user_preferences.notification_count + 1,
            positive_reactions = user_preferences.positive_reactions + %s,
            negative_reactions = user_preferences.negative_reactions + %s,
            updated_at = CURRENT_TIMESTAMP
        """

        pos_inc = 1 if reaction_type == 'positive' else 0
        neg_inc = 1 if reaction_type == 'negative' else 0

        try:
            with self.conn.cursor() as cur:
                cur.execute(query, (
                    topic, engagement_delta, pos_inc, neg_inc,
                    engagement_delta, pos_inc, neg_inc
                ))
        except Exception as e:
            logger.error(f"Failed to update user preference: {e}")

    def get_user_preferences(self, min_notifications: int = 3) -> List[Dict]:
        """
        Get user preferences sorted by engagement.

        Args:
            min_notifications: Minimum notifications to include (filter noise)

        Returns:
            List of preferences sorted by engagement
        """
        query = """
        SELECT *,
               CASE
                   WHEN engagement_score > 0.5 THEN 'high'
                   WHEN engagement_score > 0 THEN 'medium'
                   ELSE 'low'
               END as interest_level
        FROM user_preferences
        WHERE notification_count >= %s
        ORDER BY engagement_score DESC
        """

        try:
            with self.conn.cursor() as cur:
                cur.execute(query, (min_notifications,))
                return cur.fetchall()
        except Exception as e:
            logger.error(f"Failed to get user preferences: {e}")
            return []

    # ==================== Utility Methods ====================

    def cleanup_expired(self):
        """Remove expired knowledge and old cache entries."""
        queries = [
            "DELETE FROM agent_knowledge WHERE expires_at < CURRENT_TIMESTAMP",
            "DELETE FROM research_cache WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '7 days'",
            "DELETE FROM task_queue WHERE status = 'completed' AND completed_at < CURRENT_TIMESTAMP - INTERVAL '30 days'"
        ]

        try:
            with self.conn.cursor() as cur:
                for query in queries:
                    cur.execute(query)
                    logger.info(f"Cleanup: {cur.rowcount} rows affected")
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")

    def get_stats(self) -> Dict[str, int]:
        """Get database statistics."""
        stats = {}
        tables = ['agent_knowledge', 'task_queue', 'research_cache', 'user_preferences']

        try:
            with self.conn.cursor() as cur:
                for table in tables:
                    cur.execute(f"SELECT COUNT(*) as count FROM {table}")
                    stats[table] = cur.fetchone()['count']
                return stats
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {}

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            logger.info("Knowledge base connection closed")
