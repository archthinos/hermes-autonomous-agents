"""
Novelty Detector - Content Deduplication and Uniqueness Scoring

Detects duplicate or similar content using embeddings and hashing
to ensure users only receive genuinely new information.
"""

import logging
import hashlib
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import re

logger = logging.getLogger(__name__)


class NoveltyDetector:
    """
    Detects novelty and similarity in discovered content.

    Methods:
    - Exact deduplication (hashing)
    - Semantic similarity (embeddings)
    - Temporal novelty (time-based)
    - Source diversity (cross-referencing)
    """

    def __init__(
        self,
        knowledge_base,
        similarity_threshold: float = 0.85,
        novelty_decay_days: int = 30
    ):
        """
        Initialize novelty detector.

        Args:
            knowledge_base: KnowledgeBase instance
            similarity_threshold: Threshold for considering content similar (0-1)
            novelty_decay_days: Days after which content is considered "old news"
        """
        self.kb = knowledge_base
        self.similarity_threshold = similarity_threshold
        self.novelty_decay_days = novelty_decay_days

        # In-memory cache for recent hashes (performance)
        self.recent_hashes = set()
        self.cache_max_size = 1000

        logger.info(f"NoveltyDetector initialized (threshold: {similarity_threshold})")

    # ==================== Exact Deduplication ====================

    def compute_content_hash(self, content: str) -> str:
        """
        Compute hash of normalized content.

        Args:
            content: Content string

        Returns:
            SHA256 hash
        """
        # Normalize content
        normalized = self._normalize_content(content)

        # Compute hash
        return hashlib.sha256(normalized.encode('utf-8')).hexdigest()

    def is_exact_duplicate(self, content: str) -> bool:
        """
        Check if content is an exact duplicate (same hash).

        Args:
            content: Content to check

        Returns:
            True if duplicate found
        """
        content_hash = self.compute_content_hash(content)

        # Check in-memory cache first (fast)
        if content_hash in self.recent_hashes:
            logger.debug("Exact duplicate found (in-memory cache)")
            return True

        # Check database cache
        cached = self.kb.get_cached_research(content_hash, max_age_hours=24*7)
        if cached:
            logger.debug("Exact duplicate found (database)")
            self._add_to_cache(content_hash)
            return True

        # Check recent knowledge base entries
        recent = self.kb.search_knowledge(limit=100)
        for entry in recent:
            entry_hash = self.compute_content_hash(entry.get("content", ""))
            if entry_hash == content_hash:
                logger.debug("Exact duplicate found (knowledge base)")
                self._add_to_cache(content_hash)
                return True

        return False

    def _normalize_content(self, content: str) -> str:
        """Normalize content for comparison."""
        # Lowercase
        normalized = content.lower()

        # Remove extra whitespace
        normalized = re.sub(r'\s+', ' ', normalized)

        # Remove punctuation (optional - may want to keep for some use cases)
        # normalized = re.sub(r'[^\w\s]', '', normalized)

        # Strip
        normalized = normalized.strip()

        return normalized

    def _add_to_cache(self, content_hash: str):
        """Add hash to in-memory cache."""
        self.recent_hashes.add(content_hash)

        # Trim cache if too large (FIFO-ish)
        if len(self.recent_hashes) > self.cache_max_size:
            # Remove oldest (approximately - set doesn't track order)
            self.recent_hashes.pop()

    # ==================== Semantic Similarity ====================

    def compute_similarity(
        self,
        content1: str,
        content2: str,
        embeddings1: Optional[List[float]] = None,
        embeddings2: Optional[List[float]] = None
    ) -> float:
        """
        Compute semantic similarity between two pieces of content.

        Args:
            content1: First content
            content2: Second content
            embeddings1: Optional pre-computed embeddings for content1
            embeddings2: Optional pre-computed embeddings for content2

        Returns:
            Similarity score (0-1)
        """
        # If embeddings not provided, compute them
        if embeddings1 is None:
            embeddings1 = self._get_embeddings(content1)
        if embeddings2 is None:
            embeddings2 = self._get_embeddings(content2)

        if not embeddings1 or not embeddings2:
            # Fallback to simple string matching if embeddings unavailable
            return self._compute_string_similarity(content1, content2)

        # Cosine similarity
        similarity = self._cosine_similarity(embeddings1, embeddings2)
        return similarity

    def find_similar_content(
        self,
        content: str,
        embeddings: Optional[List[float]] = None,
        limit: int = 5
    ) -> List[Tuple[Dict, float]]:
        """
        Find similar content in knowledge base.

        Args:
            content: Content to search for
            embeddings: Optional pre-computed embeddings
            limit: Max results to return

        Returns:
            List of (knowledge_entry, similarity_score) tuples
        """
        if embeddings is None:
            embeddings = self._get_embeddings(content)

        if not embeddings:
            logger.warning("No embeddings available for similarity search")
            return []

        # Get recent knowledge entries
        recent = self.kb.search_knowledge(limit=200)

        # Compute similarities
        similarities = []
        for entry in recent:
            # Skip if no embeddings stored
            if not entry.get("embeddings"):
                continue

            similarity = self.compute_similarity(
                content,
                entry.get("content", ""),
                embeddings1=embeddings,
                embeddings2=entry["embeddings"]
            )

            if similarity >= self.similarity_threshold:
                similarities.append((entry, similarity))

        # Sort by similarity
        similarities.sort(key=lambda x: x[1], reverse=True)

        return similarities[:limit]

    def _get_embeddings(self, content: str) -> Optional[List[float]]:
        """
        Get embeddings for content.

        Args:
            content: Content to embed

        Returns:
            Embedding vector or None if unavailable
        """
        # TODO: Implement actual embedding generation
        # Options:
        # 1. OpenAI embeddings API
        # 2. Local model (sentence-transformers)
        # 3. Anthropic embeddings (if available)

        # For now, return None (will fallback to string similarity)
        logger.debug("Embedding generation not yet implemented")
        return None

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Compute cosine similarity between two vectors."""
        if len(vec1) != len(vec2):
            raise ValueError("Vectors must be same length")

        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = sum(a * a for a in vec1) ** 0.5
        magnitude2 = sum(b * b for b in vec2) ** 0.5

        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0

        return dot_product / (magnitude1 * magnitude2)

    def _compute_string_similarity(self, str1: str, str2: str) -> float:
        """
        Simple string similarity (Jaccard similarity of word sets).

        Args:
            str1: First string
            str2: Second string

        Returns:
            Similarity score (0-1)
        """
        # Tokenize and normalize
        words1 = set(self._normalize_content(str1).split())
        words2 = set(self._normalize_content(str2).split())

        if not words1 or not words2:
            return 0.0

        # Jaccard similarity
        intersection = words1 & words2
        union = words1 | words2

        return len(intersection) / len(union)

    # ==================== Novelty Scoring ====================

    def calculate_novelty_score(
        self,
        content: str,
        topic: str,
        metadata: Optional[Dict] = None
    ) -> float:
        """
        Calculate overall novelty score for content.

        Score factors:
        - Exact duplication: 0.0 (reject)
        - High similarity: 0.0-0.3 (probably seen before)
        - Medium similarity: 0.3-0.7 (related but new angle)
        - Low similarity: 0.7-1.0 (novel content)

        Args:
            content: Content to score
            topic: Content topic
            metadata: Additional metadata

        Returns:
            Novelty score (0-1)
        """
        metadata = metadata or {}

        # Check exact duplication first
        if self.is_exact_duplicate(content):
            return 0.0

        # Check semantic similarity
        similar = self.find_similar_content(content, limit=3)

        if not similar:
            # No similar content found - highly novel!
            novelty = 1.0
        else:
            # Compute novelty based on highest similarity
            max_similarity = max(sim for _, sim in similar)

            # Invert similarity to get novelty
            novelty = 1.0 - max_similarity

            # Boost if multiple similar items (indicates trending topic)
            if len(similar) >= 2:
                novelty *= 0.9  # Slight penalty for trending topics

        # Apply temporal decay
        novelty *= self._compute_temporal_novelty(topic)

        # Apply source diversity bonus
        novelty *= self._compute_source_diversity(metadata)

        return max(0.0, min(1.0, novelty))

    def _compute_temporal_novelty(self, topic: str) -> float:
        """
        Compute temporal novelty factor.

        Args:
            topic: Content topic

        Returns:
            Novelty multiplier (0.5-1.0)
        """
        # Get recent entries for this topic
        recent = self.kb.search_knowledge(topic=topic, limit=10)

        if not recent:
            return 1.0  # No recent coverage - fully novel

        # Find most recent entry
        latest_time = max(
            (datetime.fromisoformat(entry["created_at"]) for entry in recent),
            default=None
        )

        if not latest_time:
            return 1.0

        # Calculate days since last coverage
        days_since = (datetime.now() - latest_time).days

        if days_since == 0:
            return 0.5  # Already covered today
        elif days_since == 1:
            return 0.7  # Covered yesterday
        elif days_since <= 3:
            return 0.85  # Covered within 3 days
        elif days_since <= 7:
            return 0.95  # Covered within a week
        else:
            return 1.0  # Old coverage - fully novel now

    def _compute_source_diversity(self, metadata: Dict) -> float:
        """
        Compute source diversity bonus.

        Args:
            metadata: Content metadata (should include 'source')

        Returns:
            Diversity multiplier (1.0-1.2)
        """
        source = metadata.get("source", "unknown")

        # Check recent sources
        recent = self.kb.search_knowledge(limit=20)
        recent_sources = [entry.get("metadata", {}).get("source") for entry in recent]
        recent_sources = [s for s in recent_sources if s]  # Filter None

        if not recent_sources:
            return 1.1  # First source - good diversity

        # Count source frequency
        source_counts = {}
        for s in recent_sources:
            source_counts[s] = source_counts.get(s, 0) + 1

        # If this source is underrepresented, boost novelty
        if source not in source_counts:
            return 1.2  # New source - excellent diversity
        elif source_counts[source] == 1:
            return 1.1  # Rare source
        elif source_counts[source] <= 3:
            return 1.05  # Moderately common
        else:
            return 1.0  # Overrepresented source - no bonus

    # ==================== Deduplication Filters ====================

    def filter_novel_items(
        self,
        items: List[Dict],
        min_novelty: float = 0.5,
        content_key: str = "content",
        topic_key: str = "topic"
    ) -> List[Tuple[Dict, float]]:
        """
        Filter list of items to only novel ones.

        Args:
            items: List of item dicts
            min_novelty: Minimum novelty score to include
            content_key: Key for content in item dict
            topic_key: Key for topic in item dict

        Returns:
            List of (item, novelty_score) tuples
        """
        novel_items = []

        for item in items:
            content = item.get(content_key, "")
            topic = item.get(topic_key, "unknown")
            metadata = item.get("metadata", {})

            novelty = self.calculate_novelty_score(content, topic, metadata)

            if novelty >= min_novelty:
                novel_items.append((item, novelty))
            else:
                logger.debug(f"Filtered out low-novelty item (score: {novelty:.2f}): {content[:50]}...")

        # Sort by novelty score
        novel_items.sort(key=lambda x: x[1], reverse=True)

        logger.info(f"Filtered {len(items)} items -> {len(novel_items)} novel items")
        return novel_items

    def deduplicate_batch(
        self,
        items: List[Dict],
        content_key: str = "content"
    ) -> List[Dict]:
        """
        Remove exact duplicates from a batch of items.

        Args:
            items: List of item dicts
            content_key: Key for content in item dict

        Returns:
            Deduplicated list
        """
        seen_hashes = set()
        unique_items = []

        for item in items:
            content = item.get(content_key, "")
            content_hash = self.compute_content_hash(content)

            if content_hash not in seen_hashes:
                seen_hashes.add(content_hash)
                unique_items.append(item)
            else:
                logger.debug(f"Duplicate removed: {content[:50]}...")

        logger.info(f"Deduplicated {len(items)} items -> {len(unique_items)} unique")
        return unique_items

    # ==================== Statistics ====================

    def get_stats(self) -> Dict:
        """Get novelty detection statistics."""
        stats = {
            "cache_size": len(self.recent_hashes),
            "similarity_threshold": self.similarity_threshold,
            "novelty_decay_days": self.novelty_decay_days
        }

        # TODO: Add more stats (avg novelty score, duplicate rate, etc.)

        return stats

    def clear_cache(self):
        """Clear in-memory hash cache."""
        self.recent_hashes.clear()
        logger.info("Hash cache cleared")
