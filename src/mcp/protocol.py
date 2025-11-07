"""Model Context Protocol (MCP) Integration for Multi-Agent System"""

from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import logging
import json

logger = logging.getLogger(__name__)


class ToolType(Enum):
    """Types of tools available in MCP"""
    FUNCTION = "function"
    API = "api"
    DATABASE = "database"
    FILE_SYSTEM = "file_system"
    WEB = "web"
    CUSTOM = "custom"


@dataclass
class ToolParameter:
    """Represents a tool parameter"""
    name: str
    type: str
    description: str
    required: bool = True
    default: Any = None


@dataclass
class Tool:
    """Represents a tool in the MCP system"""
    name: str
    description: str
    tool_type: ToolType
    parameters: List[ToolParameter]
    handler: Callable
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'description': self.description,
            'type': self.tool_type.value,
            'parameters': [
                {
                    'name': p.name,
                    'type': p.type,
                    'description': p.description,
                    'required': p.required,
                    'default': p.default
                }
                for p in self.parameters
            ],
            'metadata': self.metadata
        }


@dataclass
class ToolCall:
    """Represents a tool call request"""
    tool_name: str
    arguments: Dict[str, Any]
    call_id: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolResult:
    """Represents the result of a tool call"""
    success: bool
    result: Any
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'success': self.success,
            'result': self.result,
            'error': self.error,
            'metadata': self.metadata
        }


class MCPToolRegistry:
    """
    Registry for MCP tools.

    Manages tool registration, discovery, and execution.
    """

    def __init__(self):
        self.tools: Dict[str, Tool] = {}
        self.execution_history: List[Dict[str, Any]] = []

        logger.info("Initialized MCPToolRegistry")

    def register_tool(
        self,
        name: str,
        description: str,
        tool_type: ToolType,
        parameters: List[ToolParameter],
        handler: Callable,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Tool:
        """Register a new tool"""
        tool = Tool(
            name=name,
            description=description,
            tool_type=tool_type,
            parameters=parameters,
            handler=handler,
            metadata=metadata or {}
        )

        self.tools[name] = tool
        logger.info(f"Registered tool: {name} (type: {tool_type.value})")

        return tool

    def unregister_tool(self, name: str) -> bool:
        """Unregister a tool"""
        if name in self.tools:
            del self.tools[name]
            logger.info(f"Unregistered tool: {name}")
            return True
        return False

    def get_tool(self, name: str) -> Optional[Tool]:
        """Get a tool by name"""
        return self.tools.get(name)

    def list_tools(self, tool_type: Optional[ToolType] = None) -> List[Tool]:
        """List all tools or filter by type"""
        if tool_type:
            return [tool for tool in self.tools.values() if tool.tool_type == tool_type]
        return list(self.tools.values())

    def get_tools_schema(self) -> List[Dict[str, Any]]:
        """Get schema for all tools (useful for LLM function calling)"""
        return [tool.to_dict() for tool in self.tools.values()]

    async def execute_tool(
        self,
        tool_call: ToolCall
    ) -> ToolResult:
        """Execute a tool call"""
        tool = self.tools.get(tool_call.tool_name)

        if not tool:
            error_msg = f"Tool not found: {tool_call.tool_name}"
            logger.error(error_msg)
            return ToolResult(
                success=False,
                result=None,
                error=error_msg
            )

        try:
            # Validate arguments
            validation_error = self._validate_arguments(tool, tool_call.arguments)
            if validation_error:
                return ToolResult(
                    success=False,
                    result=None,
                    error=validation_error
                )

            # Execute tool
            logger.info(f"Executing tool: {tool_call.tool_name}")

            if asyncio.iscoroutinefunction(tool.handler):
                result = await tool.handler(**tool_call.arguments)
            else:
                result = tool.handler(**tool_call.arguments)

            # Record execution
            self.execution_history.append({
                'tool_name': tool_call.tool_name,
                'call_id': tool_call.call_id,
                'arguments': tool_call.arguments,
                'success': True,
                'result': str(result)[:200]  # Truncate for storage
            })

            return ToolResult(
                success=True,
                result=result,
                metadata={'tool_type': tool.tool_type.value}
            )

        except Exception as e:
            error_msg = f"Error executing tool {tool_call.tool_name}: {str(e)}"
            logger.error(error_msg)

            self.execution_history.append({
                'tool_name': tool_call.tool_name,
                'call_id': tool_call.call_id,
                'arguments': tool_call.arguments,
                'success': False,
                'error': str(e)
            })

            return ToolResult(
                success=False,
                result=None,
                error=error_msg
            )

    def _validate_arguments(
        self,
        tool: Tool,
        arguments: Dict[str, Any]
    ) -> Optional[str]:
        """Validate tool call arguments"""
        # Check required parameters
        for param in tool.parameters:
            if param.required and param.name not in arguments:
                return f"Missing required parameter: {param.name}"

        # Check for unknown parameters
        valid_param_names = {p.name for p in tool.parameters}
        for arg_name in arguments.keys():
            if arg_name not in valid_param_names:
                return f"Unknown parameter: {arg_name}"

        return None

    def get_execution_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent execution history"""
        return self.execution_history[-limit:]


class MCPContextProvider:
    """
    Provides context to agents through MCP.

    Features:
    - Context injection
    - Resource management
    - State synchronization
    """

    def __init__(self):
        self.contexts: Dict[str, Dict[str, Any]] = {}
        self.resources: Dict[str, Any] = {}

        logger.info("Initialized MCPContextProvider")

    def register_context(
        self,
        context_id: str,
        context_data: Dict[str, Any]
    ):
        """Register a new context"""
        self.contexts[context_id] = context_data
        logger.info(f"Registered context: {context_id}")

    def get_context(self, context_id: str) -> Optional[Dict[str, Any]]:
        """Get context by ID"""
        return self.contexts.get(context_id)

    def update_context(
        self,
        context_id: str,
        updates: Dict[str, Any]
    ):
        """Update existing context"""
        if context_id in self.contexts:
            self.contexts[context_id].update(updates)
            logger.info(f"Updated context: {context_id}")

    def delete_context(self, context_id: str) -> bool:
        """Delete a context"""
        if context_id in self.contexts:
            del self.contexts[context_id]
            logger.info(f"Deleted context: {context_id}")
            return True
        return False

    def register_resource(
        self,
        resource_id: str,
        resource: Any,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Register a resource (file, API, database connection, etc.)"""
        self.resources[resource_id] = {
            'resource': resource,
            'metadata': metadata or {}
        }
        logger.info(f"Registered resource: {resource_id}")

    def get_resource(self, resource_id: str) -> Optional[Any]:
        """Get resource by ID"""
        resource_data = self.resources.get(resource_id)
        return resource_data['resource'] if resource_data else None

    def list_available_contexts(self) -> List[str]:
        """List all available context IDs"""
        return list(self.contexts.keys())

    def list_available_resources(self) -> List[str]:
        """List all available resource IDs"""
        return list(self.resources.keys())


class MCPServer:
    """
    MCP Server for multi-agent system.

    Coordinates tool execution, context management, and agent communication.
    """

    def __init__(
        self,
        tool_registry: Optional[MCPToolRegistry] = None,
        context_provider: Optional[MCPContextProvider] = None
    ):
        self.tool_registry = tool_registry or MCPToolRegistry()
        self.context_provider = context_provider or MCPContextProvider()
        self.active_sessions: Dict[str, Dict[str, Any]] = {}

        logger.info("Initialized MCPServer")

    async def handle_tool_call(
        self,
        tool_call: ToolCall,
        session_id: Optional[str] = None
    ) -> ToolResult:
        """Handle a tool call from an agent"""
        # Track session if provided
        if session_id:
            if session_id not in self.active_sessions:
                self.active_sessions[session_id] = {'tool_calls': []}
            self.active_sessions[session_id]['tool_calls'].append(tool_call.tool_name)

        # Execute tool
        result = await self.tool_registry.execute_tool(tool_call)

        return result

    def get_available_tools(self) -> List[Dict[str, Any]]:
        """Get schema of all available tools"""
        return self.tool_registry.get_tools_schema()

    def provide_context(
        self,
        agent_id: str,
        context_data: Dict[str, Any]
    ):
        """Provide context to an agent"""
        context_id = f"agent_{agent_id}"
        self.context_provider.register_context(context_id, context_data)

    def get_agent_context(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get context for an agent"""
        context_id = f"agent_{agent_id}"
        return self.context_provider.get_context(context_id)

    def get_server_stats(self) -> Dict[str, Any]:
        """Get server statistics"""
        return {
            'total_tools': len(self.tool_registry.tools),
            'active_sessions': len(self.active_sessions),
            'total_contexts': len(self.context_provider.contexts),
            'total_resources': len(self.context_provider.resources),
            'recent_executions': len(self.tool_registry.execution_history)
        }
