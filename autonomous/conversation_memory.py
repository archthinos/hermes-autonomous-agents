"""
Conversation Memory - Persistent conversation history with user preferences
"""

import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)


class ConversationMemory:
    """
    Manages conversation history and user preferences in PostgreSQL.

    Features:
    - Store conversation messages with context
    - Track user preferences and opinions
    - Retrieve relevant conversation history
    - Maintain user profile
    """

    def __init__(self, knowledge_base):
        """Initialize conversation memory with knowledge base."""
        self.kb = knowledge_base
        self._ensure_schema()
        logger.info("ConversationMemory initialized")

    def _ensure_schema(self):
        """Create conversation tables if they don't exist."""
        with self.kb.get_connection() as conn:
            with conn.cursor() as cur:
                # Conversation messages table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS conversation_messages (
                        id SERIAL PRIMARY KEY,
                        user_id BIGINT NOT NULL,
                        message_type VARCHAR(20) NOT NULL,  -- 'user' or 'assistant'
                        content TEXT NOT NULL,
                        agent_name VARCHAR(100),
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        metadata JSONB DEFAULT '{}'
                    )
                """)

                # User preferences table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS user_preferences (
                        id SERIAL PRIMARY KEY,
                        user_id BIGINT NOT NULL UNIQUE,
                        preferences JSONB DEFAULT '{}',
                        interests JSONB DEFAULT '[]',
                        communication_style VARCHAR(50) DEFAULT 'balanced',
                        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                # User opinions/beliefs table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS user_opinions (
                        id SERIAL PRIMARY KEY,
                        user_id BIGINT NOT NULL,
                        topic VARCHAR(200) NOT NULL,
                        opinion TEXT NOT NULL,
                        confidence FLOAT DEFAULT 0.5,
                        mentioned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                # Create indexes
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_conv_user_time
                    ON conversation_messages(user_id, timestamp DESC)
                """)
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_opinions_user_topic
                    ON user_opinions(user_id, topic)
                """)

                conn.commit()

    def add_message(self, user_id: int, message_type: str, content: str,
                    agent_name: Optional[str] = None, metadata: Optional[Dict] = None):
        """Add a message to conversation history."""
        with self.kb.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO conversation_messages
                    (user_id, message_type, content, agent_name, metadata)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                """, (user_id, message_type, content, agent_name,
                      json.dumps(metadata or {})))
                message_id = cur.fetchone()[0]
                conn.commit()
                return message_id

    def get_recent_messages(self, user_id: int, limit: int = 10) -> List[Dict]:
        """Get recent conversation messages for context."""
        with self.kb.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT message_type, content, agent_name, timestamp, metadata
                    FROM conversation_messages
                    WHERE user_id = %s
                    ORDER BY timestamp DESC
                    LIMIT %s
                """, (user_id, limit))

                messages = []
                for row in cur.fetchall():
                    messages.append({
                        'role': row[0],  # 'user' or 'assistant'
                        'content': row[1],
                        'agent_name': row[2],
                        'timestamp': row[3].isoformat() if row[3] else None,
                        'metadata': row[4]
                    })

                # Return in chronological order (oldest first)
                return list(reversed(messages))

    def get_conversation_context(self, user_id: int, max_messages: int = 6) -> str:
        """
        Build conversation context string for LLM prompt.
        Returns formatted conversation history.
        """
        messages = self.get_recent_messages(user_id, max_messages)

        if not messages:
            return "No previous conversation history."

        context_lines = ["Recent conversation:"]
        for msg in messages:
            role = "User" if msg['role'] == 'user' else "Assistant"
            agent_info = f" ({msg['agent_name']})" if msg['agent_name'] else ""
            context_lines.append(f"{role}{agent_info}: {msg['content']}")

        return "\n".join(context_lines)

    def update_user_preferences(self, user_id: int, preferences: Dict):
        """Update user preferences."""
        with self.kb.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO user_preferences (user_id, preferences, last_updated)
                    VALUES (%s, %s, CURRENT_TIMESTAMP)
                    ON CONFLICT (user_id)
                    DO UPDATE SET
                        preferences = user_preferences.preferences || EXCLUDED.preferences,
                        last_updated = CURRENT_TIMESTAMP
                """, (user_id, json.dumps(preferences)))
                conn.commit()

    def add_user_interest(self, user_id: int, interest: str):
        """Add an interest to user profile."""
        with self.kb.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO user_preferences (user_id, interests, last_updated)
                    VALUES (%s, %s, CURRENT_TIMESTAMP)
                    ON CONFLICT (user_id)
                    DO UPDATE SET
                        interests = (
                            SELECT jsonb_agg(DISTINCT elem)
                            FROM jsonb_array_elements(
                                user_preferences.interests || EXCLUDED.interests
                            ) elem
                        ),
                        last_updated = CURRENT_TIMESTAMP
                """, (user_id, json.dumps([interest])))
                conn.commit()

    def record_opinion(self, user_id: int, topic: str, opinion: str, confidence: float = 0.7):
        """Record user's opinion on a topic."""
        with self.kb.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO user_opinions (user_id, topic, opinion, confidence, updated_at)
                    VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
                    ON CONFLICT (user_id, topic)
                    DO UPDATE SET
                        opinion = EXCLUDED.opinion,
                        confidence = EXCLUDED.confidence,
                        updated_at = CURRENT_TIMESTAMP
                """, (user_id, topic, opinion, confidence))
                conn.commit()

    def get_user_opinions(self, user_id: int, topic: Optional[str] = None) -> List[Dict]:
        """Get user's recorded opinions."""
        with self.kb.get_connection() as conn:
            with conn.cursor() as cur:
                if topic:
                    cur.execute("""
                        SELECT topic, opinion, confidence, updated_at
                        FROM user_opinions
                        WHERE user_id = %s AND topic ILIKE %s
                        ORDER BY updated_at DESC
                    """, (user_id, f"%{topic}%"))
                else:
                    cur.execute("""
                        SELECT topic, opinion, confidence, updated_at
                        FROM user_opinions
                        WHERE user_id = %s
                        ORDER BY updated_at DESC
                        LIMIT 20
                    """, (user_id,))

                opinions = []
                for row in cur.fetchall():
                    opinions.append({
                        'topic': row[0],
                        'opinion': row[1],
                        'confidence': row[2],
                        'updated_at': row[3].isoformat() if row[3] else None
                    })
                return opinions

    def get_user_profile(self, user_id: int) -> Dict:
        """Get complete user profile with preferences and interests."""
        with self.kb.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT preferences, interests, communication_style
                    FROM user_preferences
                    WHERE user_id = %s
                """, (user_id,))

                row = cur.fetchone()
                if row:
                    return {
                        'preferences': row[0],
                        'interests': row[1],
                        'communication_style': row[2]
                    }
                else:
                    # Return default profile
                    return {
                        'preferences': {},
                        'interests': [],
                        'communication_style': 'balanced'
                    }

    def get_user_summary(self, user_id: int) -> str:
        """
        Generate a summary of user for LLM context.
        Includes preferences, interests, and key opinions.
        """
        profile = self.get_user_profile(user_id)
        opinions = self.get_user_opinions(user_id)

        summary_parts = []

        # Interests
        if profile['interests']:
            interests_str = ", ".join(profile['interests'])
            summary_parts.append(f"User interests: {interests_str}")

        # Communication style
        summary_parts.append(f"Preferred communication style: {profile['communication_style']}")

        # Key opinions
        if opinions:
            summary_parts.append("User's known opinions:")
            for op in opinions[:5]:  # Top 5 most recent
                summary_parts.append(f"  - {op['topic']}: {op['opinion']}")

        # Preferences
        if profile['preferences']:
            summary_parts.append(f"Other preferences: {json.dumps(profile['preferences'])}")

        return "\n".join(summary_parts) if summary_parts else "New user, no profile data yet."

    def extract_and_store_insights(self, user_id: int, user_message: str):
        """
        Analyze user message for insights (interests, opinions).
        This is a simple keyword-based approach - could be enhanced with LLM.
        """
        message_lower = user_message.lower()

        # Detect interests
        interest_keywords = {
            'ai': 'artificial intelligence',
            'crypto': 'cryptocurrency',
            'bitcoin': 'cryptocurrency',
            'ethereum': 'cryptocurrency',
            'programming': 'software development',
            'python': 'python programming',
            'javascript': 'javascript programming',
            'machine learning': 'machine learning',
            'blockchain': 'blockchain technology'
        }

        for keyword, interest in interest_keywords.items():
            if keyword in message_lower:
                self.add_user_interest(user_id, interest)

        # Detect strong opinions (simple heuristic)
        opinion_indicators = ['i think', 'i believe', 'in my opinion', 'i feel that']
        for indicator in opinion_indicators:
            if indicator in message_lower:
                # Extract topic and opinion (simplified)
                # In production, use NLP or LLM for better extraction
                logger.info(f"Detected opinion in message from user {user_id}")
                # For now, just log - could enhance with LLM extraction
