"""
Ollama Chat Client - Intelligent conversation with agent routing
"""

import logging
import os
import httpx
from typing import List, Dict, Optional
import yaml

logger = logging.getLogger(__name__)


class OllamaChat:
    """
    Chat interface using Ollama API with intelligent agent routing.

    Features:
    - Route messages to appropriate specialized agents
    - Maintain conversation context
    - Use agent personalities from SOUL.md
    - Generate contextually aware responses
    """

    def __init__(self, conversation_memory):
        """Initialize Ollama chat client."""
        self.memory = conversation_memory
        self.base_url = os.getenv("OLLAMA_BASE_URL", "https://api.ollama.ai")
        self.api_key = os.getenv("OLLAMA_API_KEY")
        self.model = "llama3.1:8b"

        # Load agent configurations
        self.agents = self._load_agent_configs()
        logger.info(f"OllamaChat initialized with {len(self.agents)} agents")

    def _load_agent_configs(self) -> Dict:
        """Load agent configurations and personalities."""
        agents = {}
        agent_dirs = [
            "orchestrator", "ai_researcher", "software_dev",
            "crypto_agent", "productivity", "social_monitor", "web_researcher"
        ]

        for agent_name in agent_dirs:
            try:
                # Load config
                config_path = f"agents/{agent_name}/config.yaml"
                soul_path = f"agents/{agent_name}/SOUL.md"

                config = {}
                soul = ""

                if os.path.exists(config_path):
                    with open(config_path, 'r') as f:
                        config = yaml.safe_load(f) or {}

                if os.path.exists(soul_path):
                    with open(soul_path, 'r') as f:
                        soul = f.read()

                agents[agent_name] = {
                    'config': config,
                    'soul': soul,
                    'personality': config.get('personality', 'helpful')
                }
            except Exception as e:
                logger.warning(f"Could not load agent {agent_name}: {e}")

        return agents

    def route_to_agent(self, message: str) -> str:
        """
        Determine which agent should handle the message.
        Returns agent_name.
        """
        message_lower = message.lower()

        # Keywords for routing
        routing_rules = {
            'ai_researcher': ['ai', 'llm', 'model', 'research', 'paper', 'arxiv', 'machine learning', 'neural'],
            'software_dev': ['code', 'github', 'programming', 'developer', 'repository', 'software', 'bug', 'feature'],
            'crypto_agent': ['crypto', 'bitcoin', 'ethereum', 'btc', 'eth', 'blockchain', 'defi', 'market', 'price'],
            'productivity': ['task', 'todo', 'schedule', 'calendar', 'remind', 'plan', 'organize'],
            'social_monitor': ['twitter', 'reddit', 'hacker news', 'social', 'trending', 'discussion'],
            'web_researcher': ['search', 'find', 'lookup', 'research', 'investigate']
        }

        # Score each agent
        scores = {}
        for agent, keywords in routing_rules.items():
            score = sum(1 for kw in keywords if kw in message_lower)
            if score > 0:
                scores[agent] = score

        # Return agent with highest score, or orchestrator as default
        if scores:
            return max(scores, key=scores.get)
        return 'orchestrator'

    async def chat(self, user_id: int, message: str) -> str:
        """
        Process user message and generate response.

        Args:
            user_id: Telegram user ID
            message: User's message

        Returns:
            Assistant's response
        """
        try:
            # Store user message
            self.memory.add_message(user_id, 'user', message)

            # Extract insights from message
            self.memory.extract_and_store_insights(user_id, message)

            # Route to appropriate agent
            agent_name = self.route_to_agent(message)
            logger.info(f"Routing message to agent: {agent_name}")

            # Build context
            context = self._build_context(user_id, agent_name, message)

            # Call Ollama API
            response = await self._call_ollama(context)

            # Store assistant response
            self.memory.add_message(user_id, 'assistant', response, agent_name)

            return response

        except Exception as e:
            logger.error(f"Chat error: {e}", exc_info=True)
            return "Prepáčte, vyskytla sa chyba pri spracovaní vašej správy. Skúste to prosím znova."

    def _build_context(self, user_id: int, agent_name: str, current_message: str) -> List[Dict]:
        """Build conversation context for LLM."""
        messages = []

        # System prompt with agent personality
        agent_info = self.agents.get(agent_name, {})
        personality = agent_info.get('personality', 'helpful')
        soul = agent_info.get('soul', '')

        system_prompt = f"""You are a specialized AI assistant.

Agent Role: {agent_name}
Personality: {personality}

{soul[:500] if soul else ''}

User Profile:
{self.memory.get_user_summary(user_id)}

Guidelines:
- Remember the user's previous messages and preferences
- Provide helpful, accurate, and contextually relevant information
- Be conversational and engaging
- Communicate in Slovak if the user uses Slovak, otherwise English
- If you don't know something, admit it honestly
"""

        messages.append({
            "role": "system",
            "content": system_prompt
        })

        # Add conversation history
        history = self.memory.get_recent_messages(user_id, limit=4)
        for msg in history:
            messages.append({
                "role": msg['role'],
                "content": msg['content']
            })

        # Current message
        messages.append({
            "role": "user",
            "content": current_message
        })

        return messages

    async def _call_ollama(self, messages: List[Dict]) -> str:
        """Call Ollama API to generate response."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "top_p": 0.9,
            }
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/v1/chat/completions",
                headers=headers,
                json=payload
            )
            response.raise_for_status()

            data = response.json()

            # Extract response based on API format
            if "choices" in data and len(data["choices"]) > 0:
                return data["choices"][0]["message"]["content"]
            elif "message" in data:
                return data["message"]["content"]
            else:
                logger.error(f"Unexpected API response format: {data}")
                return "Prepáčte, nedostal som správnu odpoveď z AI modelu."
