"""
Goal Generator - Proactive Task and Goal Creation

Analyzes user conversation history, interests, and patterns to generate
proactive research goals for agents without explicit user requests.
"""

import logging
from typing import List, Dict, Optional, Set
from datetime import datetime, timedelta
from collections import Counter
import re

logger = logging.getLogger(__name__)


class GoalGenerator:
    """
    Generates proactive research goals based on user context and interests.

    Analyzes:
    - User conversation history
    - Engagement patterns
    - Current events and trends
    - Knowledge gaps
    - Temporal patterns (time-sensitive goals)
    """

    def __init__(self, knowledge_base):
        """
        Initialize goal generator.

        Args:
            knowledge_base: KnowledgeBase instance
        """
        self.kb = knowledge_base

        # Goal generation rules per agent
        self.agent_goals = {
            "ai_researcher": {
                "topics": ["AI", "ML", "LLM", "neural", "model", "GPT", "Claude"],
                "sources": ["ArXiv", "Papers with Code", "Hugging Face"],
                "frequency": "3x_daily"  # 9:00, 15:00, 21:00
            },
            "software_dev": {
                "topics": ["GitHub", "framework", "library", "tool", "API"],
                "sources": ["GitHub Trending", "Hacker News", "Dev.to"],
                "frequency": "2x_daily"  # 10:00, 18:00
            },
            "crypto_agent": {
                "topics": ["Bitcoin", "Ethereum", "DeFi", "crypto", "blockchain"],
                "sources": ["Polymarket", "CoinGecko", "DeFiLlama"],
                "frequency": "3x_daily"  # 8:00, 14:00, 20:00
            },
            "productivity": {
                "topics": ["task", "deadline", "calendar", "meeting"],
                "sources": ["Calendar", "Tasks", "Notes"],
                "frequency": "2x_daily"  # 7:00, 19:00
            },
            "social_monitor": {
                "topics": ["Twitter", "Reddit", "HN", "discussion"],
                "sources": ["Twitter/X", "Reddit", "Hacker News"],
                "frequency": "2x_daily"  # 11:00, 17:00
            },
            "web_researcher": {
                "topics": [],  # Reactive only
                "sources": [],
                "frequency": "on_demand"
            }
        }

        logger.info("GoalGenerator initialized")

    # ==================== Main Goal Generation ====================

    def generate_goals_for_agent(
        self,
        agent_name: str,
        context: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Generate proactive goals for a specific agent.

        Args:
            agent_name: Name of agent
            context: Additional context (time of day, recent events, etc.)

        Returns:
            List of goal dicts with 'goal', 'priority', 'metadata'
        """
        if agent_name not in self.agent_goals:
            logger.warning(f"Unknown agent: {agent_name}")
            return []

        context = context or {}
        goals = []

        # Get user preferences for this agent's domain
        preferences = self._get_relevant_preferences(agent_name)

        # Get recent conversation topics
        recent_topics = self._extract_recent_topics()

        # Generate goals based on agent type
        if agent_name == "ai_researcher":
            goals.extend(self._generate_ai_research_goals(preferences, recent_topics))
        elif agent_name == "software_dev":
            goals.extend(self._generate_dev_goals(preferences, recent_topics))
        elif agent_name == "crypto_agent":
            goals.extend(self._generate_crypto_goals(preferences, recent_topics))
        elif agent_name == "productivity":
            goals.extend(self._generate_productivity_goals(context))
        elif agent_name == "social_monitor":
            goals.extend(self._generate_social_goals(preferences, recent_topics))

        # Add temporal context goals
        goals.extend(self._generate_temporal_goals(agent_name, context))

        # Rank by priority
        goals.sort(key=lambda g: g.get("priority", 50), reverse=True)

        logger.info(f"Generated {len(goals)} goals for {agent_name}")
        return goals

    # ==================== Agent-Specific Goal Generators ====================

    def _generate_ai_research_goals(
        self,
        preferences: List[Dict],
        recent_topics: Set[str]
    ) -> List[Dict]:
        """Generate AI research goals."""
        goals = []

        # Default goal: Check latest ArXiv papers
        goals.append({
            "goal": "Search ArXiv for new AI/ML papers from the last 24 hours",
            "priority": 60,
            "metadata": {"source": "arxiv", "timeframe": "24h"}
        })

        # Check Hugging Face trending
        goals.append({
            "goal": "Scan Hugging Face for trending models and datasets",
            "priority": 55,
            "metadata": {"source": "huggingface"}
        })

        # If user interested in specific AI topics
        high_interest = [p for p in preferences if p.get("engagement_score", 0) > 0.5]
        for pref in high_interest[:3]:  # Top 3
            topic = pref["topic"]
            goals.append({
                "goal": f"Deep dive into recent developments in {topic}",
                "priority": 70,
                "metadata": {"topic": topic, "user_driven": True}
            })

        # If recent conversation mentioned AI companies
        ai_companies = ["OpenAI", "Anthropic", "Google", "Meta", "DeepMind"]
        mentioned_companies = [c for c in ai_companies if c.lower() in recent_topics]
        for company in mentioned_companies:
            goals.append({
                "goal": f"Check {company} blog and announcements for recent posts",
                "priority": 65,
                "metadata": {"company": company}
            })

        return goals

    def _generate_dev_goals(
        self,
        preferences: List[Dict],
        recent_topics: Set[str]
    ) -> List[Dict]:
        """Generate software development goals."""
        goals = []

        # Default: GitHub Trending
        goals.append({
            "goal": "Analyze GitHub Trending repositories across all languages",
            "priority": 60,
            "metadata": {"source": "github"}
        })

        # Hacker News scan
        goals.append({
            "goal": "Scan Hacker News front page and Show HN for dev tools",
            "priority": 55,
            "metadata": {"source": "hackernews"}
        })

        # Language-specific if user showed interest
        languages = ["JavaScript", "Python", "Rust", "Go", "TypeScript"]
        for lang in languages:
            if lang.lower() in recent_topics:
                goals.append({
                    "goal": f"Find trending {lang} projects and tools",
                    "priority": 65,
                    "metadata": {"language": lang}
                })

        # Framework-specific
        frameworks = ["React", "Vue", "Django", "FastAPI", "Next.js"]
        for fw in frameworks:
            if fw.lower() in recent_topics:
                goals.append({
                    "goal": f"Check for {fw} updates, releases, and discussions",
                    "priority": 60,
                    "metadata": {"framework": fw}
                })

        return goals

    def _generate_crypto_goals(
        self,
        preferences: List[Dict],
        recent_topics: Set[str]
    ) -> List[Dict]:
        """Generate crypto/finance goals."""
        goals = []

        # Default: Market snapshot
        goals.append({
            "goal": "Get crypto market snapshot: BTC, ETH, SOL prices and movements",
            "priority": 60,
            "metadata": {"type": "market_snapshot"}
        })

        # DeFi overview
        goals.append({
            "goal": "Check DeFi TVL changes across major protocols",
            "priority": 50,
            "metadata": {"type": "defi"}
        })

        # Polymarket trending
        goals.append({
            "goal": "Scan Polymarket for trending prediction markets on AI, crypto, tech",
            "priority": 55,
            "metadata": {"source": "polymarket"}
        })

        # Specific assets if mentioned
        assets = ["BTC", "ETH", "SOL", "Bitcoin", "Ethereum", "Solana"]
        for asset in assets:
            if asset.lower() in recent_topics:
                goals.append({
                    "goal": f"Deep analysis of {asset}: price, volume, on-chain metrics",
                    "priority": 70,
                    "metadata": {"asset": asset}
                })

        return goals

    def _generate_productivity_goals(self, context: Dict) -> List[Dict]:
        """Generate productivity goals."""
        goals = []
        current_hour = datetime.now().hour

        # Morning briefing (if called around 7 AM)
        if 6 <= current_hour <= 8:
            goals.append({
                "goal": "Generate morning briefing: today's tasks, calendar, priorities",
                "priority": 80,
                "metadata": {"type": "morning_briefing"}
            })

        # Evening review (if called around 7 PM)
        elif 18 <= current_hour <= 20:
            goals.append({
                "goal": "Generate evening review: progress, tomorrow's plan",
                "priority": 80,
                "metadata": {"type": "evening_review"}
            })

        # Midday check
        else:
            goals.append({
                "goal": "Check for upcoming deadlines and calendar conflicts",
                "priority": 50,
                "metadata": {"type": "midday_check"}
            })

        return goals

    def _generate_social_goals(
        self,
        preferences: List[Dict],
        recent_topics: Set[str]
    ) -> List[Dict]:
        """Generate social media monitoring goals."""
        goals = []

        # Default scans
        goals.append({
            "goal": "Scan Twitter/X for trending AI and tech discussions",
            "priority": 55,
            "metadata": {"source": "twitter", "topics": ["AI", "tech"]}
        })

        goals.append({
            "goal": "Check Reddit r/programming and r/MachineLearning hot posts",
            "priority": 55,
            "metadata": {"source": "reddit"}
        })

        goals.append({
            "goal": "Monitor Hacker News for high-engagement discussions",
            "priority": 50,
            "metadata": {"source": "hackernews"}
        })

        # Topic-specific if user interested
        if "crypto" in recent_topics or "bitcoin" in recent_topics:
            goals.append({
                "goal": "Scan crypto Twitter and r/CryptoCurrency for market sentiment",
                "priority": 60,
                "metadata": {"topic": "crypto"}
            })

        return goals

    def _generate_temporal_goals(
        self,
        agent_name: str,
        context: Dict
    ) -> List[Dict]:
        """
        Generate time-sensitive goals based on context.

        Args:
            agent_name: Agent name
            context: Current context (time, day of week, etc.)

        Returns:
            List of temporal goals
        """
        goals = []
        now = datetime.now()

        # Monday morning: Weekly planning
        if now.weekday() == 0 and 6 <= now.hour <= 9:
            if agent_name == "productivity":
                goals.append({
                    "goal": "Generate weekly plan and goal setting",
                    "priority": 90,
                    "metadata": {"type": "weekly_planning"}
                })

        # Friday evening: Weekly review
        if now.weekday() == 4 and 17 <= now.hour <= 20:
            if agent_name == "productivity":
                goals.append({
                    "goal": "Generate weekly accomplishments review",
                    "priority": 85,
                    "metadata": {"type": "weekly_review"}
                })

        # Sunday evening: Week prep
        if now.weekday() == 6 and 18 <= now.hour <= 21:
            goals.append({
                "goal": "Prepare overview of coming week's events and tasks",
                "priority": 75,
                "metadata": {"type": "week_preview"}
            })

        return goals

    # ==================== Helper Methods ====================

    def _get_relevant_preferences(self, agent_name: str) -> List[Dict]:
        """Get user preferences relevant to this agent."""
        all_prefs = self.kb.get_user_preferences()
        agent_topics = self.agent_goals.get(agent_name, {}).get("topics", [])

        # Filter preferences matching agent's topics
        relevant = []
        for pref in all_prefs:
            topic_lower = pref["topic"].lower()
            if any(agent_topic.lower() in topic_lower for agent_topic in agent_topics):
                relevant.append(pref)

        return relevant

    def _extract_recent_topics(self, days: int = 7) -> Set[str]:
        """
        Extract topics from recent knowledge base entries.

        Args:
            days: Look back N days

        Returns:
            Set of lowercase topic keywords
        """
        # Get recent knowledge
        recent_knowledge = self.kb.search_knowledge(limit=50)

        topics = set()
        for entry in recent_knowledge:
            # Extract keywords from content and topic
            content = entry.get("content", "") + " " + entry.get("topic", "")
            words = re.findall(r'\b[A-Za-z]{3,}\b', content)  # Words 3+ chars
            topics.update(w.lower() for w in words)

        return topics

    def _identify_knowledge_gaps(self, agent_name: str) -> List[str]:
        """
        Identify knowledge gaps that should be researched.

        Args:
            agent_name: Agent name

        Returns:
            List of gap descriptions
        """
        gaps = []

        # Get agent's recent discoveries
        recent = self.kb.search_knowledge(agent_name=agent_name, limit=20)

        if not recent:
            gaps.append("No recent discoveries - perform initial scan")
            return gaps

        # Check for staleness (no discoveries in 24h)
        latest = max((datetime.fromisoformat(r["created_at"]) for r in recent), default=None)
        if latest and (datetime.now() - latest) > timedelta(hours=24):
            gaps.append("No recent updates - scan for new information")

        # Check topic coverage
        covered_topics = set(r["topic"] for r in recent)
        expected_topics = set(self.agent_goals.get(agent_name, {}).get("topics", []))
        missing_topics = expected_topics - covered_topics

        for topic in missing_topics:
            gaps.append(f"No recent coverage of {topic}")

        return gaps

    # ==================== Conversational Goal Generation ====================

    def generate_followup_questions(
        self,
        recent_discoveries: List[Dict],
        max_questions: int = 3
    ) -> List[str]:
        """
        Generate follow-up questions based on recent discoveries.

        Args:
            recent_discoveries: List of recent knowledge entries
            max_questions: Max questions to generate

        Returns:
            List of question strings
        """
        questions = []

        # Analyze discoveries for interesting leads
        for discovery in recent_discoveries[:5]:
            content = discovery.get("content", "")
            topic = discovery.get("topic", "")

            # Look for incomplete information
            if "more details" in content.lower() or "upcoming" in content.lower():
                questions.append(f"Should I research more about {topic}?")

            # Look for comparisons or alternatives
            if "vs" in content or "alternative" in content.lower():
                questions.append(f"Would you like me to compare options for {topic}?")

            # Look for time-sensitive info
            if "soon" in content.lower() or "upcoming" in content.lower():
                questions.append(f"Should I monitor {topic} for updates?")

            if len(questions) >= max_questions:
                break

        return questions[:max_questions]

    # ==================== Statistics ====================

    def get_goal_generation_stats(self) -> Dict:
        """Get statistics about goal generation."""
        stats = {
            "agents_configured": len(self.agent_goals),
            "total_topics": sum(len(cfg["topics"]) for cfg in self.agent_goals.values())
        }

        # Count recent goals created (from task queue)
        # TODO: Add task_queue querying here

        return stats
