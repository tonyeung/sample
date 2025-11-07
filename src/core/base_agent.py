"""Base Agent Framework for Multi-Agent System"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class Message:
    """Represents a message in the multi-agent system"""
    role: str  # 'user', 'agent', 'system', 'tool'
    content: str
    sender: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    requires_human_approval: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary"""
        return {
            'role': self.role,
            'content': self.content,
            'sender': self.sender,
            'timestamp': self.timestamp.isoformat(),
            'metadata': self.metadata,
            'requires_human_approval': self.requires_human_approval
        }


@dataclass
class AgentResponse:
    """Response from an agent"""
    success: bool
    content: str
    action_taken: Optional[str] = None
    requires_approval: bool = False
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseAgent(ABC):
    """Base class for all agents in the system"""

    def __init__(
        self,
        name: str,
        role: str,
        system_prompt: str,
        tools: Optional[List[Callable]] = None,
        memory_enabled: bool = True
    ):
        self.name = name
        self.role = role
        self.system_prompt = system_prompt
        self.tools = tools or []
        self.memory_enabled = memory_enabled
        self.conversation_history: List[Message] = []
        self.context: Dict[str, Any] = {}

        logger.info(f"Initialized agent: {name} with role: {role}")

    @abstractmethod
    async def process_message(self, message: Message) -> AgentResponse:
        """Process an incoming message and return a response"""
        pass

    def add_to_memory(self, message: Message):
        """Add message to agent's memory"""
        if self.memory_enabled:
            self.conversation_history.append(message)
            logger.debug(f"{self.name} added message to memory from {message.sender}")

    def get_context(self, max_messages: int = 10) -> List[Dict[str, Any]]:
        """Get recent conversation context"""
        recent_messages = self.conversation_history[-max_messages:]
        return [msg.to_dict() for msg in recent_messages]

    def update_context(self, key: str, value: Any):
        """Update agent's context with new information"""
        self.context[key] = value
        logger.debug(f"{self.name} updated context: {key}")

    def clear_memory(self):
        """Clear conversation history"""
        self.conversation_history.clear()
        logger.info(f"{self.name} cleared memory")

    def register_tool(self, tool: Callable):
        """Register a new tool for the agent"""
        self.tools.append(tool)
        logger.info(f"{self.name} registered new tool: {tool.__name__}")

    def get_capabilities(self) -> Dict[str, Any]:
        """Return agent's capabilities"""
        return {
            'name': self.name,
            'role': self.role,
            'tools': [tool.__name__ for tool in self.tools],
            'memory_enabled': self.memory_enabled
        }

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name='{self.name}', role='{self.role}')>"
