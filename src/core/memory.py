"""Memory and Context Management for Multi-Agent System"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict
import json


@dataclass
class MemoryEntry:
    """Represents a single memory entry"""
    content: str
    embedding: Optional[List[float]] = None
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    importance: float = 0.5  # 0.0 to 1.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            'content': self.content,
            'timestamp': self.timestamp.isoformat(),
            'metadata': self.metadata,
            'importance': self.importance
        }


class ContextualMemory:
    """Manages contextual learning and memory for agents"""

    def __init__(self, max_short_term: int = 50, max_long_term: int = 500):
        self.short_term_memory: List[MemoryEntry] = []
        self.long_term_memory: List[MemoryEntry] = []
        self.max_short_term = max_short_term
        self.max_long_term = max_long_term
        self.learned_patterns: Dict[str, Any] = {}
        self.entity_memory: Dict[str, List[str]] = defaultdict(list)

    def add_short_term(self, content: str, metadata: Optional[Dict] = None, importance: float = 0.5):
        """Add entry to short-term memory"""
        entry = MemoryEntry(
            content=content,
            metadata=metadata or {},
            importance=importance
        )

        self.short_term_memory.append(entry)

        # Maintain max size
        if len(self.short_term_memory) > self.max_short_term:
            # Move important memories to long-term
            self._consolidate_memory()

    def add_long_term(self, content: str, metadata: Optional[Dict] = None, importance: float = 0.7):
        """Add entry to long-term memory"""
        entry = MemoryEntry(
            content=content,
            metadata=metadata or {},
            importance=importance
        )

        self.long_term_memory.append(entry)

        # Maintain max size
        if len(self.long_term_memory) > self.max_long_term:
            # Remove least important memories
            self.long_term_memory.sort(key=lambda x: x.importance, reverse=True)
            self.long_term_memory = self.long_term_memory[:self.max_long_term]

    def _consolidate_memory(self):
        """Move important short-term memories to long-term"""
        # Sort by importance
        self.short_term_memory.sort(key=lambda x: x.importance, reverse=True)

        # Move top 20% to long-term
        consolidate_count = len(self.short_term_memory) // 5
        for entry in self.short_term_memory[:consolidate_count]:
            if entry.importance > 0.6:  # Only consolidate important memories
                self.long_term_memory.append(entry)

        # Keep only recent short-term memories
        self.short_term_memory = self.short_term_memory[-self.max_short_term:]

    def search_memory(self, query: str, top_k: int = 5) -> List[MemoryEntry]:
        """Search both short-term and long-term memory (keyword-based)"""
        all_memories = self.short_term_memory + self.long_term_memory

        # Simple keyword matching (can be enhanced with embeddings)
        query_lower = query.lower()
        scored_memories = []

        for memory in all_memories:
            content_lower = memory.content.lower()
            score = 0.0

            # Keyword matching
            query_words = query_lower.split()
            for word in query_words:
                if word in content_lower:
                    score += 1.0

            # Boost by importance
            score *= memory.importance

            if score > 0:
                scored_memories.append((score, memory))

        # Sort by score
        scored_memories.sort(key=lambda x: x[0], reverse=True)

        return [memory for _, memory in scored_memories[:top_k]]

    def learn_pattern(self, pattern_name: str, pattern_data: Any):
        """Store a learned pattern"""
        self.learned_patterns[pattern_name] = {
            'data': pattern_data,
            'learned_at': datetime.now().isoformat(),
            'usage_count': 0
        }

    def recall_pattern(self, pattern_name: str) -> Optional[Any]:
        """Recall a learned pattern"""
        if pattern_name in self.learned_patterns:
            self.learned_patterns[pattern_name]['usage_count'] += 1
            return self.learned_patterns[pattern_name]['data']
        return None

    def track_entity(self, entity_name: str, information: str):
        """Track information about specific entities"""
        self.entity_memory[entity_name].append(information)

    def get_entity_info(self, entity_name: str) -> List[str]:
        """Get all tracked information about an entity"""
        return self.entity_memory.get(entity_name, [])

    def get_context_summary(self, max_items: int = 10) -> str:
        """Get a summary of current context"""
        recent_short_term = self.short_term_memory[-max_items:]
        summary_parts = ["Recent context:"]

        for entry in recent_short_term:
            summary_parts.append(f"- {entry.content[:100]}...")

        return "\n".join(summary_parts)

    def export_memory(self) -> Dict[str, Any]:
        """Export memory state"""
        return {
            'short_term': [entry.to_dict() for entry in self.short_term_memory],
            'long_term': [entry.to_dict() for entry in self.long_term_memory],
            'learned_patterns': self.learned_patterns,
            'entity_memory': dict(self.entity_memory)
        }

    def clear_all(self):
        """Clear all memory"""
        self.short_term_memory.clear()
        self.long_term_memory.clear()
        self.learned_patterns.clear()
        self.entity_memory.clear()
